import asyncio
import io
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from fastapi import UploadFile
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.ingestion.provenance import SourceProvenance


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
    assert (canonical.source_id, canonical.isbn) == ("doi:10.1000/abc.def", "9781402894626")
    assert canonical.url == "https://example.org/Guide"
    assert legacy.source_id == equivalent.source_id
    assert ipv6.url == "https://[2001:db8::1]:8443/Guide"
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
        "url": "https://example.org/guide", "doi": "10.1000/guide", "license": "CC-BY-4.0",
        "reviewer": "Lic. Reviewer", "review_date": "2026-07-01",
    }
    point = MagicMock(score=0.91, payload=payload)
    client = MagicMock()
    client.query_points.return_value.points = [point]
    monkeypatch.setattr(module, "get_qdrant", lambda: client)
    monkeypatch.setattr(module, "generate_embedding", lambda _query: [0.1])
    metadata = module.Retriever().search("evidence")[0]["metadata"]
    for key in payload.keys() - {"text"}:
        assert metadata[key] == payload[key]
    assert metadata["source"] == "knowledge_base/guide.md"

@pytest.mark.parametrize("filename", ["../../Original Guide.md", r"..\..\Original Guide.md"])
def test_upload_preserves_original_filename(monkeypatch, filename):
    auth = ModuleType("app.core.auth.dependencies")
    auth.require_role = lambda _roles: lambda: None
    user = ModuleType("app.models.user")
    user.User = object
    monkeypatch.setitem(sys.modules, "app.core.auth.dependencies", auth)
    monkeypatch.setitem(sys.modules, "app.models.user", user)
    from app.api.v1 import knowledge
    captured = {}
    monkeypatch.setattr(
        knowledge,
        "ingest_file",
        lambda path, metadata_override: captured.update(metadata_override) or {"file": path},
    )
    upload = UploadFile(filename=filename, file=io.BytesIO(b"source"))
    response = asyncio.run(
        knowledge.ingest_document(file=upload, source_key="clinic/guide", current_user=object())
    )
    assert captured["original_source_name"] == "Original Guide.md"
    assert captured["original_source_path"] == "Original Guide.md"
    assert (captured["identity_scope"], captured["source_key"]) == ("upload", "clinic/guide")
    assert response["data"]["file"] == "Original Guide.md"
