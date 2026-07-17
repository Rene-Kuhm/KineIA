import os
import uuid

import pytest
from app.core.ingestion import pipeline
from app.db.hybrid_collection import provision_hybrid_collection
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


def test_live_hybrid_provisioning_is_exact_and_idempotent():
    if os.getenv("QDRANT_INTEGRATION") != "1":
        pytest.skip("QDRANT_INTEGRATION=1 is required")
    client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"),
                          check_compatibility=False)
    suffix = uuid.uuid4().hex
    legacy, hybrid = f"legacy_{suffix}", f"hybrid_{suffix}"
    kwargs = dict(legacy_collection_name=legacy, collection_name=hybrid,
                  dense_vector_name="dense", sparse_vector_name="sparse", dimensions=1024)
    try:
        created, created_code = provision_hybrid_collection(client, **kwargs)
        compatible, compatible_code = provision_hybrid_collection(client, **kwargs)
        assert client.info().version == "1.18.2"
        assert (created["status"], created_code) == ("created", 0)
        assert (compatible["status"], compatible_code) == ("compatible", 0)
        assert compatible["actions"] == []
        assert compatible["observed"]["payload_indexes"] == {
            "area": "keyword", "evidence_level": "keyword", "source_id": "keyword"}
        assert client.collection_exists(legacy) is False
        assert all(alias.collection_name != hybrid for alias in client.get_aliases().aliases)
    finally:
        if client.collection_exists(hybrid):
            client.delete_collection(hybrid)
def test_live_dual_write_converges_and_removes_stale_points(tmp_path, monkeypatch):
    if os.getenv("QDRANT_INTEGRATION") != "1":
        pytest.skip("QDRANT_INTEGRATION=1 is required")
    client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"),
                          check_compatibility=False)
    suffix = uuid.uuid4().hex
    legacy, hybrid = f"legacy_{suffix}", f"hybrid_{suffix}"
    kwargs = dict(legacy_collection_name=legacy, collection_name=hybrid,
                  dense_vector_name="dense", sparse_vector_name="sparse", dimensions=1024)
    document = tmp_path / "guide.md"
    metadata = dict(source_key="live/dual-guide", original_source_name="guide.md",
                    original_source_path="guide.md", reviewer="Lic. Test",
                    review_date="2026-07-17", area="traumatology", evidence_level="guide")
    try:
        client.create_collection(collection_name=legacy,
                                 vectors_config=VectorParams(size=1024, distance=Distance.COSINE))
        assert provision_hybrid_collection(client, **kwargs)[1] == 0
        monkeypatch.setattr(pipeline, "qdrant_client", client)
        for name, value in (("qdrant_collection", legacy), ("qdrant_hybrid_collection", hybrid)):
            monkeypatch.setattr(pipeline.settings, name, value)
        monkeypatch.setattr(pipeline.settings, "qdrant_write_mode", "dual")
        monkeypatch.setattr(pipeline, "generate_embeddings",
                            lambda texts: [[0.1] * 1024 for _ in texts])
        document.write_text("Rehabilitación inicial de rodilla.", encoding="utf-8")
        pipeline.ingest_file(str(document), metadata)
        document.write_text("Rehabilitación actualizada de hombro.", encoding="utf-8")
        pipeline.ingest_file(str(document), metadata)
        old = client.scroll(legacy, limit=10, with_vectors=True)[0]
        new = client.scroll(hybrid, limit=10, with_vectors=True)[0]
        assert len(old) == len(new) == 1
        assert (old[0].id, old[0].payload) == (new[0].id, new[0].payload)
        assert new[0].payload["text"] == "Rehabilitación actualizada de hombro."
        assert set(new[0].vector) == {"dense", "sparse"}
    finally:
        for collection in (legacy, hybrid):
            if client.collection_exists(collection):
                client.delete_collection(collection)
