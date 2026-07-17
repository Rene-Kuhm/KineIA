from types import SimpleNamespace
from unittest.mock import MagicMock

from qdrant_client.models import Distance, VectorParams


def existing_client(vectors=None, point_count=27):
    client = MagicMock()
    client.info.return_value.version = "1.18.2"
    client.collection_exists.return_value = True
    client.get_collection.return_value.config.params.vectors = vectors or VectorParams(
        size=1024, distance=Distance.COSINE
    )
    client.count.return_value = SimpleNamespace(count=point_count)
    return client


def test_preflight_reports_compatible_collection_without_mutation():
    from app.db.qdrant_preflight import run_preflight

    client = existing_client()
    report, exit_code = run_preflight(client, "kineia_knowledge", 1024)

    assert (exit_code, report["status"], report["server_version"]) == (
        0,
        "compatible",
        "1.18.2",
    )
    assert report["collection"] == {
        "name": "kineia_knowledge",
        "exists": True,
        "vector_shape": "unnamed",
        "vector_names": [],
        "dimensions": 1024,
        "distance": "Cosine",
        "exact_point_count": 27,
    }
    client.create_collection.assert_not_called()
    client.delete_collection.assert_not_called()
    client.upsert.assert_not_called()
    client.count.assert_called_once_with(collection_name="kineia_knowledge", exact=True)


def test_preflight_reports_missing_collection_as_safe_to_initialize():
    from app.db.qdrant_preflight import run_preflight

    client = existing_client()
    client.collection_exists.return_value = False
    report, exit_code = run_preflight(client, "kineia_knowledge", 1024)

    assert (exit_code, report["status"]) == (0, "missing")
    assert report["collection"]["exists"] is False
    assert report["collection"]["exact_point_count"] == 0
    client.get_collection.assert_not_called()
    client.count.assert_not_called()
    client.create_collection.assert_not_called()


def test_preflight_returns_nonzero_for_incompatible_collection():
    from app.db.qdrant_preflight import run_preflight

    client = existing_client(VectorParams(size=384, distance=Distance.DOT))
    report, exit_code = run_preflight(client, "kineia_knowledge", 1024)

    assert (exit_code, report["status"]) == (1, "incompatible")
    assert report["collection"]["dimensions"] == 384
    assert report["collection"]["distance"] == "Dot"
    assert report["collection"]["exact_point_count"] == 27


def test_preflight_sanitizes_unreachable_errors():
    from app.db.qdrant_preflight import run_preflight

    client = MagicMock()
    client.info.side_effect = RuntimeError("token=secret")
    report, exit_code = run_preflight(client, "kineia_knowledge", 1024)

    assert (exit_code, report["status"]) == (2, "unreachable")
    assert report["server_version"] is None
    assert report["collection"]["exists"] is None
    assert report["error"] == "Qdrant is unreachable"
    assert "secret" not in str(report)
