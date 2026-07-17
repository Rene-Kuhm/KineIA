from unittest.mock import MagicMock

import fitz
import pytest
from app.core.ingestion.extractors.pdf import extract_pdf
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


def pdf_file(tmp_path, page_texts):
    path = tmp_path / "guide.pdf"
    if path.exists():
        path.unlink()
    document = fitz.open()
    for text in page_texts:
        page = document.new_page()
        if text is None:
            pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 2, 2), False)
            pixmap.clear_with(255)
            page.insert_image(fitz.Rect(72, 72, 144, 144), pixmap=pixmap)
        elif text:
            page.insert_textbox(fitz.Rect(72, 72, 520, 770), text)
    document.save(path)
    document.close()
    return path


def test_extractor_preserves_physical_page_numbers_including_blanks(tmp_path):
    extracted = extract_pdf(str(pdf_file(tmp_path, ["First", "", "Third"])))
    pages = [(page["page_number"], page["text"].strip()) for page in extracted["pages"]]
    assert pages == [(1, "First"), (2, ""), (3, "Third")]


def test_ingestion_chunks_each_nonempty_page_with_computed_locators(tmp_path, monkeypatch):
    from app.core.ingestion import pipeline

    batches = []
    monkeypatch.setattr(
        pipeline, "generate_embeddings",
        lambda texts: batches.append(texts) or [[0.1] for _ in texts],
    )
    path = pdf_file(tmp_path, ["First page", "", "Third page"])
    prepared = pipeline.prepare_ingestion(str(path), {
        "original_source_name": "guide.pdf", "original_source_path": r"C:\private\guide.pdf",
        "page_start": 99, "page_end": 100, "section_heading": "Forged",
        "section_path": ["Forged"], "chunk_index": 77, "fragment_hash": "forged",
    })
    payloads = [point.payload for point in prepared.points]

    assert [(item["page_start"], item["page_end"]) for item in payloads] == [(1, 1), (3, 3)]
    assert [
        (item["chunk_index"], item["section_heading"], item["section_path"])
        for item in payloads
    ] == [
        (0, None, None), (1, None, None),
    ]
    assert batches == [[item["text"] for item in payloads]]
    assert all(
        "private" not in repr(item) and item["fragment_hash"] != "forged"
        for item in payloads
    )


def test_long_page_produces_multiple_chunks_with_the_same_page(tmp_path, monkeypatch):
    from app.core.ingestion import pipeline

    monkeypatch.setattr(pipeline.settings, "chunk_size", 10)
    monkeypatch.setattr(pipeline.settings, "chunk_overlap", 0)
    monkeypatch.setattr(pipeline, "generate_embeddings", lambda texts: [[0.1] for _ in texts])
    prepared = pipeline.prepare_ingestion(str(pdf_file(tmp_path, ["word " * 80])))
    assert len(prepared.points) > 1
    pages = [(point.payload["page_start"], point.payload["page_end"]) for point in prepared.points]
    assert pages == [(1, 1)] * len(prepared.points)
    assert [point.payload["chunk_index"] for point in prepared.points] == list(
        range(len(prepared.points))
    )


def test_empty_and_image_only_pages_do_not_invent_text_or_embeddings(tmp_path, monkeypatch):
    from app.core.ingestion import pipeline

    path = pdf_file(tmp_path, [None, ""])
    assert all(not page["text"].strip() for page in extract_pdf(str(path))["pages"])
    monkeypatch.setattr(
        pipeline, "generate_embeddings",
        lambda _texts: pytest.fail("embedded empty PDF"),
    )
    prepared = pipeline.prepare_ingestion(str(path))
    assert prepared.points == [] and prepared.result["status"] == "empty"


@pytest.mark.parametrize("fails", [False, True])
def test_extractor_reads_each_page_once_and_always_closes(monkeypatch, fails):
    page, document = MagicMock(), MagicMock()
    page.get_text.return_value = "Evidence"
    if fails:
        page.get_text.side_effect = RuntimeError("extract failed")
    document.__enter__.return_value = document
    document.__iter__.return_value = iter([page])
    monkeypatch.setattr(fitz, "open", lambda _path: document)

    if fails:
        with pytest.raises(RuntimeError, match="extract failed"):
            extract_pdf("guide.pdf")
    else:
        assert extract_pdf("guide.pdf")["pages"][0]["text"] == "Evidence"
    page.get_text.assert_called_once_with()
    document.__exit__.assert_called_once()


def test_changed_pdf_reingestion_removes_stale_page_chunks(tmp_path, monkeypatch):
    from app.core.ingestion import pipeline

    client = QdrantClient(":memory:")
    client.create_collection(
        pipeline.settings.qdrant_collection,
        vectors_config=VectorParams(size=1, distance=Distance.COSINE),
    )
    monkeypatch.setattr(pipeline, "qdrant_client", client)
    monkeypatch.setattr(pipeline, "generate_embeddings", lambda texts: [[0.1] for _ in texts])
    path = pdf_file(tmp_path, ["Original", "Stable"])
    pipeline.ingest_file(str(path))
    old_ids = {point.id for point in client.scroll(pipeline.settings.qdrant_collection)[0]}

    pdf_file(tmp_path, ["Updated", "Stable"])
    pipeline.ingest_file(str(path))
    records = client.scroll(pipeline.settings.qdrant_collection, limit=10)[0]
    assert len(records) == 2 and {point.payload["page_start"] for point in records} == {1, 2}
    assert old_ids.isdisjoint({point.id for point in records})
    assert "Updated" in repr(records) and "Original" not in repr(records)
    assert str(tmp_path) not in repr([point.payload for point in records])


@pytest.mark.parametrize("mode", ["legacy", "dual"])
def test_empty_reingestion_cleans_every_write_collection_idempotently(
    tmp_path, monkeypatch, mode,
):
    from app.core.ingestion import pipeline

    client = QdrantClient(":memory:")
    collections = [pipeline.settings.qdrant_collection]
    if mode == "dual":
        collections.append(pipeline.settings.qdrant_hybrid_collection)
    for collection in collections:
        client.create_collection(
            collection, vectors_config=VectorParams(size=1, distance=Distance.COSINE),
        )
    monkeypatch.setattr(pipeline, "qdrant_client", client)
    monkeypatch.setattr(pipeline.settings, "qdrant_write_mode", mode)
    monkeypatch.setattr(pipeline, "generate_embeddings", lambda texts: [[0.1] for _ in texts])
    path = pdf_file(tmp_path, ["Stale evidence"])
    prepared = pipeline.prepare_ingestion(str(path))
    for collection in collections:
        client.upsert(collection, prepared.points)

    pdf_file(tmp_path, [None])
    monkeypatch.setattr(pipeline, "generate_embeddings", lambda _texts: pytest.fail("embedded"))
    upsert = MagicMock(wraps=client.upsert)
    monkeypatch.setattr(client, "upsert", upsert)
    for _ in range(2):
        assert pipeline.ingest_file(str(path))["status"] == "empty"
    upsert.assert_not_called()
    assert all(not client.scroll(collection)[0] for collection in collections)
