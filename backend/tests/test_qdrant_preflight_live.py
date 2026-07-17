import os
import uuid

import pytest
from app.db.qdrant_preflight import run_preflight
from qdrant_client import QdrantClient


def test_live_preflight_is_read_only_against_pinned_qdrant():
    if os.getenv("QDRANT_INTEGRATION") != "1":
        pytest.skip("QDRANT_INTEGRATION=1 is required")

    client = QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        check_compatibility=False,
    )
    collection = f"preflight_missing_{uuid.uuid4().hex}"

    report, exit_code = run_preflight(client, collection, 1024)

    assert exit_code == 0
    assert report["status"] == "missing"
    assert report["server_version"] == "1.18.2"
    assert client.collection_exists(collection) is False
