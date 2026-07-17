import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from qdrant_client.models import (
    Distance,
    Modifier,
    PayloadIndexInfo,
    PayloadSchemaType,
    SparseVectorParams,
    VectorParams,
)


def test_root_command_and_custom_hybrid_configuration(tmp_path):
    from app.config import Settings
    root = Path(__file__).parents[2]
    env_example = (root / ".env.example").read_text(encoding="utf-8")
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")
    command = "uv run --project backend --no-sync python backend/scripts/provision_hybrid.py"
    assert command in env_example
    keys = "qdrant_hybrid_collection qdrant_dense_vector_name qdrant_sparse_vector_name".split()
    assert all(f"- {key.upper()}=${{{key.upper()}:-" in compose for key in keys)
    env = tmp_path / ".env"
    env.write_text(
        "QDRANT_HYBRID_COLLECTION=custom\nQDRANT_DENSE_VECTOR_NAME=d\n"
        "QDRANT_SPARSE_VECTOR_NAME=s\n"
    )
    settings = Settings(_env_file=env)
    assert [getattr(settings, key) for key in keys] == ["custom", "d", "s"]


def provision(client, collection="knowledge_v2"):
    from app.db.hybrid_collection import provision_hybrid_collection
    return provision_hybrid_collection(
        client,
        legacy_collection_name="legacy", collection_name=collection,
        dense_vector_name="dense", sparse_vector_name="sparse",
        dimensions=1024,
    )


def collection_info(
    *, size=1024, distance=Distance.COSINE, modifier=Modifier.IDF,
    dense_name="dense", sparse_name="sparse", fields=None, schema=PayloadSchemaType.KEYWORD,
):
    fields = ("area", "evidence_level", "source_id") if fields is None else fields
    vectors = {dense_name: VectorParams(size=size, distance=distance)}
    sparse = {sparse_name: SparseVectorParams(modifier=modifier)}
    params = SimpleNamespace(vectors=vectors, sparse_vectors=sparse)
    payload = {field: PayloadIndexInfo(data_type=schema, points=0) for field in fields}
    return SimpleNamespace(config=SimpleNamespace(params=params), payload_schema=payload)


def test_missing_collection_is_created_with_exact_hybrid_schema_and_indexes():
    client = MagicMock()
    client.collection_exists.return_value = False
    report, exit_code = provision(client)
    assert (report["status"], exit_code) == ("created", 0)
    args = client.create_collection.call_args.kwargs
    dense = args["vectors_config"]["dense"]
    sparse = args["sparse_vectors_config"]["sparse"]
    assert (dense.size, dense.distance) == (1024, Distance.COSINE)
    assert sparse.modifier == Modifier.IDF
    calls = client.create_payload_index.call_args_list
    assert {call.kwargs["field_name"] for call in calls} == {"area", "evidence_level", "source_id"}
    assert {call.kwargs["field_schema"] for call in calls} == {PayloadSchemaType.KEYWORD}
    client.delete_collection.assert_not_called()
    client.update_collection_aliases.assert_not_called()


def test_exact_existing_schema_is_idempotent():
    client = MagicMock()
    client.collection_exists.return_value = True
    client.get_collection.return_value = collection_info()
    report, exit_code = provision(client)
    assert (report["status"], report["actions"], exit_code) == ("compatible", [], 0)
    assert not any((client.create_collection.called, client.create_payload_index.called,
                    client.delete_collection.called, client.update_collection_aliases.called))


def test_incompatible_existing_schema_fails_without_mutation():
    for info in (
        collection_info(size=384), collection_info(distance=Distance.DOT),
        collection_info(modifier=None), collection_info(schema=PayloadSchemaType.TEXT),
        collection_info(dense_name="other"), collection_info(sparse_name="other"),
    ):
        client = MagicMock()
        client.collection_exists.return_value = True
        client.get_collection.return_value = info
        report, exit_code = provision(client)
        assert (report["status"], exit_code) == ("incompatible", 1)
        assert not any((client.create_collection.called, client.create_payload_index.called,
                        client.delete_collection.called))


def test_missing_required_indexes_are_added_without_recreating_collection():
    client = MagicMock()
    client.collection_exists.return_value = True
    client.get_collection.return_value = collection_info(fields=("area",))
    report, exit_code = provision(client)
    assert (report["status"], exit_code) == ("updated", 0)
    fields = [c.kwargs["field_name"] for c in client.create_payload_index.call_args_list]
    assert fields == ["evidence_level", "source_id"]
    client.create_collection.assert_not_called()


def test_runtime_errors_are_sanitized():
    client = MagicMock()
    client.collection_exists.side_effect = RuntimeError("token=super-secret")
    report, exit_code = provision(client)
    assert (report["status"], exit_code) == ("error", 2)
    assert "super-secret" not in json.dumps(report)


def test_legacy_collection_name_is_refused_without_server_calls():
    client = MagicMock()
    report, exit_code = provision(client, collection="legacy")
    assert (report["status"], exit_code) == ("refused", 1)
    assert client.mock_calls == []
