import hashlib
from unittest.mock import MagicMock

import pytest
from app.core.ingestion.provenance import SourceProvenance
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


def upload_metadata(name="guide.md"):
    return {"original_source_name": name, "original_source_path": name, "identity_scope": "upload"}

def test_source_identity_normalizes_canonical_ids_and_safe_fallbacks():
    canonical_meta = upload_metadata("Guide.md") | {
        "doi": " HTTPS://doi.org/10.1000/ABC.Def ", "isbn": "978-1-4028-9462-6",
        "url": "HTTPS://Example.org/Guide/#section",
    }
    legacy_meta = upload_metadata("Legacy.md") | {
        "doi": "invalid", "isbn": "123", "url": "javascript:alert(1)", "year": "bad",
        "original_source_path": r"knowledge_base\Legacy.md",
    }
    canonical = SourceProvenance.from_content(b"content", canonical_meta)
    legacy = SourceProvenance.from_content("legacy", legacy_meta)
    equivalent = SourceProvenance.from_content(
        "legacy",
        upload_metadata("Legacy.md") | {"original_source_path": "KNOWLEDGE_BASE/legacy.md"},
    )
    ipv6 = SourceProvenance.from_content(
        "ipv6",
        upload_metadata("guide.md") | {"url": "HTTPS://[2001:db8::1]:8443/Guide/#part"},
    )
    bounded = SourceProvenance.from_content(
        "bounded",
        upload_metadata(r"C:\private\guide.md") | {"evidence_level": "x" * 2049},
    )
    assert (canonical.source_id, canonical.isbn) == ("doi:10.1000/abc.def", "9781402894626")
    assert canonical.url == "https://example.org/Guide"
    assert legacy.source_id == equivalent.source_id
    assert ipv6.url == "https://[2001:db8::1]:8443/Guide"
    assert bounded.original_source_name == "guide.md" and bounded.evidence_level is None
    assert all(SourceProvenance.from_content(
        "unsafe", upload_metadata() | {"url": value},
    ).url is None for value in (
        "file:///private/guide.md", "C:relative.md", "https://user:secret@example.org/x",
        "https://example.org/bad path", "https://example.org/bad\npath", "https://example.org/bad\\path",
    ))
    assert not any((legacy.doi, legacy.url, legacy.year, legacy.license, legacy.reviewer))
    years = {
        value: SourceProvenance.from_content("year", upload_metadata() | {"year": value}).year
        for value in (999, 1000, 9999, 10000)
    }
    assert years == {999: None, 1000: 1000, 9999: 9999, 10000: None}
@pytest.fixture
def pipeline(monkeypatch):
    from app.core.ingestion import pipeline
    monkeypatch.setattr(pipeline, "generate_embeddings", lambda texts: [[0.1] for _ in texts])
    return pipeline

def test_prepared_payload_uses_computed_locators_and_preserves_factual_metadata(
    tmp_path, pipeline,
):
    document = tmp_path / "guide.md"
    document.write_text("# Safe section\nEvidence.", encoding="utf-8")
    untrusted = upload_metadata("guide.md") | {
        "original_source_path": r"C:\private\guide.md", "chunk_index": 99,
        "fragment_hash": "forged", "section_heading": "Forged",
        "section_path": ["Forged"], "page_start": 7, "page_end": 8,
        "title": r"C:\private\secret.md",
        "url": "HTTPS://Example.org/Guide/#part", "doi": "doi:10.1000/ABC",
        "isbn": "978-1-4028-9462-6", "publication_date": "2025-04-01",
        "review_date": "2026-07-16", "evidence_level": "systematic-review",
    }

    prepared = pipeline.prepare_ingestion(str(document), untrusted)
    payload = prepared.points[0].payload
    repeated = pipeline.prepare_ingestion(
        str(document), untrusted | {"chunk_index": -1, "fragment_hash": "different"},
    )

    assert (prepared.points[0].id, payload) == (repeated.points[0].id, repeated.points[0].payload)
    assert payload["fragment_hash"] == hashlib.sha256(payload["text"].encode()).hexdigest()
    assert (payload["chunk_index"], payload["section_heading"], payload["section_path"]) == (
        0, "Safe section", ["Safe section"],
    )
    assert payload["page_start"] is payload["page_end"] is None
    assert payload["title"] == "guide.md" and "private" not in repr(payload)
    assert not {"original_source_path", "source_file", "file_name"} & payload.keys()
    assert (payload["url"], payload["doi"], payload["isbn"]) == (
        "https://example.org/Guide", "10.1000/abc", "9781402894626",
    )
    assert payload["publication_date"] == "2025-04-01"
    assert payload["review_date"] == "2026-07-16"
    assert payload["evidence_level"] == "systematic-review"
def test_rechunking_same_version_removes_obsolete_chunk(tmp_path, pipeline, monkeypatch):
    module = pipeline
    client = QdrantClient(":memory:")
    client.create_collection(
        module.settings.qdrant_collection,
        vectors_config=VectorParams(size=1, distance=Distance.COSINE),
    )
    monkeypatch.setattr(module, "qdrant_client", client)
    chunks = [{"text": "one"}, {"text": "two"}]
    monkeypatch.setattr(module, "chunk_text", lambda *_a, **_k: chunks)
    document = tmp_path / "guide.md"
    document.write_text("same content", encoding="utf-8")
    metadata = upload_metadata() | {"source_key": "repo/guide", "license": "CC-BY-4.0"}
    module.ingest_file(str(document), metadata)
    original_ids = {point.id for point in client.scroll(module.settings.qdrant_collection)[0]}
    module.ingest_file(str(document), metadata)
    repeated = client.scroll(module.settings.qdrant_collection)[0]
    assert {point.id for point in repeated} == original_ids
    assert repeated[0].payload["license"] == "CC-BY-4.0"
    chunks.pop()
    module.ingest_file(str(document), metadata)
    assert len(client.scroll(module.settings.qdrant_collection, limit=10)[0]) == 1
    same_name_upload = upload_metadata("same.md")
    document.write_text("unrelated A", encoding="utf-8")
    module.ingest_file(str(document), same_name_upload)
    document.write_text("unrelated B", encoding="utf-8")
    module.ingest_file(str(document), same_name_upload)
    keyed_upload = same_name_upload | {"source_key": "clinic/guide"}
    document.write_text("keyed version A", encoding="utf-8")
    keyed = module.ingest_file(str(document), keyed_upload)
    document.write_text("keyed version B", encoding="utf-8")
    module.ingest_file(str(document), same_name_upload | {"source_key": "CLINIC\\GUIDE"})
    records = client.scroll(module.settings.qdrant_collection, limit=10)[0]
    assert len(records) == 4
    assert sum(point.payload["source_id"] == keyed["source_id"] for point in records) == 1
def test_retriever_exposes_canonical_provenance(monkeypatch):
    from app.services.rag import retriever as module
    payload = {
        "text": "statement", "source_id": "doi:10.1000/guide", "source_version": "2026",
        "original_source_name": "guide.md", "original_source_path": "knowledge_base/guide.md",
        "source_file": r"C:\private\guide.md", "chunk_index": 4,
        "fragment_hash": "b" * 64, "section_heading": "Exercise",
        "section_path": ["Knee", "Exercise"], "page_start": None, "page_end": None,
        "url": "https://example.org/guide", "doi": "10.1000/guide", "license": "CC-BY-4.0",
        "reviewer": "Lic. Reviewer", "review_date": "2026-07-01",
    }
    point = MagicMock(score=0.91, payload=payload)
    client = MagicMock()
    client.query_points.return_value.points = [point]
    monkeypatch.setattr(module, "get_qdrant", lambda: client)
    monkeypatch.setattr(module, "generate_embedding", lambda _query: [0.1])
    metadata = module.Retriever().search("evidence")[0]["metadata"]
    hidden = {"text", "original_source_path", "source_file"}
    for key in payload.keys() - hidden - {"page_start", "page_end"}:
        assert metadata[key] == payload[key]
    assert metadata["source"] == "guide.md"
    assert not hidden - {"text"} & metadata.keys()
    assert "private" not in repr(metadata)
