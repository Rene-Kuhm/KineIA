from collections.abc import Mapping
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance


def describe_vectors(vectors: Any) -> dict[str, Any]:
    named = isinstance(vectors, Mapping)
    vector_names = sorted(vectors) if named else []
    vector = next(iter(vectors.values())) if named and len(vectors) == 1 else vectors
    distance = getattr(vector, "distance", None)
    return {
        "vector_shape": "named" if named else "unnamed",
        "vector_names": vector_names,
        "dimensions": getattr(vector, "size", None),
        "distance": distance.value if distance else None,
    }


def is_legacy_compatible(vector_report: dict[str, Any], expected_dimensions: int) -> bool:
    return (
        vector_report["vector_shape"] == "unnamed"
        and vector_report["dimensions"] == expected_dimensions
        and vector_report["distance"] == Distance.COSINE.value
    )


def run_preflight(
    client: QdrantClient,
    collection_name: str,
    expected_dimensions: int,
) -> tuple[dict[str, Any], int]:
    """Inspect Qdrant compatibility without mutating server state."""
    expected = {
        "vector_shape": "unnamed",
        "dimensions": expected_dimensions,
        "distance": Distance.COSINE.value,
    }
    collection = {
        "name": collection_name,
        "exists": None,
        "vector_shape": None,
        "vector_names": [],
        "dimensions": None,
        "distance": None,
        "exact_point_count": None,
    }
    try:
        server_version = client.info().version
        exists = client.collection_exists(collection_name)
        collection["exists"] = exists
        if not exists:
            collection["exact_point_count"] = 0
            return {
                "status": "missing",
                "server_version": server_version,
                "collection": collection,
                "expected": expected,
            }, 0

        vectors = client.get_collection(collection_name).config.params.vectors
        point_count = client.count(collection_name=collection_name, exact=True).count
        vector_report = describe_vectors(vectors)
        compatible = is_legacy_compatible(vector_report, expected_dimensions)
        collection.update(vector_report | {"exact_point_count": point_count})
        return {
            "status": "compatible" if compatible else "incompatible",
            "server_version": server_version,
            "collection": collection,
            "expected": expected,
        }, 0 if compatible else 1
    except Exception:
        return {
            "status": "unreachable",
            "server_version": None,
            "collection": collection,
            "expected": expected,
            "error": "Qdrant is unreachable",
        }, 2
