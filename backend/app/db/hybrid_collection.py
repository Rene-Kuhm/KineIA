from collections.abc import Mapping
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    Modifier,
    PayloadSchemaType,
    SparseVectorParams,
    VectorParams,
)

REQUIRED_INDEXES = ("area", "evidence_level", "source_id")


def _inspect_schema(
    info: Any, dense_name: str, sparse_name: str, dimensions: int
) -> tuple[dict[str, Any], bool, list[str]]:
    params = info.config.params
    vectors = params.vectors if isinstance(params.vectors, Mapping) else {}
    sparse_vectors = (
        params.sparse_vectors if isinstance(params.sparse_vectors, Mapping) else {}
    )
    dense = vectors.get(dense_name)
    sparse = sparse_vectors.get(sparse_name)
    payload = info.payload_schema or {}
    indexes = {
        field: getattr(payload[field].data_type, "value", payload[field].data_type)
        for field in REQUIRED_INDEXES
        if field in payload
    }
    observed = {
        "dense_names": sorted(vectors),
        "dense_dimensions": getattr(dense, "size", None),
        "dense_distance": getattr(getattr(dense, "distance", None), "value", None),
        "sparse_names": sorted(sparse_vectors),
        "sparse_modifier": getattr(getattr(sparse, "modifier", None), "value", None),
        "payload_indexes": indexes,
    }
    compatible = (
        set(vectors) == {dense_name}
        and observed["dense_dimensions"] == dimensions
        and observed["dense_distance"] == Distance.COSINE.value
        and set(sparse_vectors) == {sparse_name}
        and observed["sparse_modifier"] == Modifier.IDF.value
        and all(value == PayloadSchemaType.KEYWORD.value for value in indexes.values())
    )
    missing = [field for field in REQUIRED_INDEXES if field not in indexes]
    return observed, compatible, missing


def hybrid_collection_is_compatible(
    client: QdrantClient, *, collection_name: str, dense_name: str,
    sparse_name: str, dimensions: int,
) -> bool:
    if not client.collection_exists(collection_name):
        return False
    _observed, compatible, missing = _inspect_schema(
        client.get_collection(collection_name), dense_name, sparse_name, dimensions
    )
    return compatible and not missing


def provision_hybrid_collection(
    client: QdrantClient,
    *,
    legacy_collection_name: str,
    collection_name: str,
    dense_vector_name: str,
    sparse_vector_name: str,
    dimensions: int,
) -> tuple[dict[str, Any], int]:
    """Explicitly provision v2 without changing the active legacy collection."""
    expected = {
        "dense": {"name": dense_vector_name, "dimensions": dimensions, "distance": "Cosine"},
        "sparse": {"name": sparse_vector_name, "modifier": "idf"},
        "keyword_indexes": list(REQUIRED_INDEXES),
    }
    report: dict[str, Any] = {
        "collection": collection_name,
        "legacy_collection": legacy_collection_name,
        "expected": expected,
        "actions": [],
    }
    if collection_name == legacy_collection_name:
        return report | {
            "status": "refused",
            "error": "Hybrid collection must be distinct from the active legacy collection",
        }, 1
    try:
        exists = client.collection_exists(collection_name)
        if exists:
            observed, compatible, missing = _inspect_schema(
                client.get_collection(collection_name),
                dense_vector_name,
                sparse_vector_name,
                dimensions,
            )
            report["observed"] = observed
            if not compatible:
                return report | {
                    "status": "incompatible",
                    "error": "Existing hybrid collection is incompatible; no changes were made",
                }, 1
        else:
            client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    dense_vector_name: VectorParams(size=dimensions, distance=Distance.COSINE)
                },
                sparse_vectors_config={
                    sparse_vector_name: SparseVectorParams(modifier=Modifier.IDF)
                },
            )
            report["actions"].append("created_collection")
            missing = list(REQUIRED_INDEXES)
        for field in missing:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD,
                wait=True,
            )
            report["actions"].append(f"created_index:{field}")
        status = "created" if not exists else "updated" if missing else "compatible"
        return report | {"status": status}, 0
    except Exception:
        return report | {
            "status": "error",
            "error": "Hybrid collection provisioning failed; no destructive action was taken",
        }, 2
