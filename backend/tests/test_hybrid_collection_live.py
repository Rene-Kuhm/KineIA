import os
import uuid

import pytest
from app.db.hybrid_collection import provision_hybrid_collection
from qdrant_client import QdrantClient


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
