import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.config import settings
from app.db.qdrant_preflight import describe_vectors, is_legacy_compatible

logger = logging.getLogger(__name__)

qdrant_client = QdrantClient(url=settings.qdrant_url, check_compatibility=False)


async def init_qdrant_collection():
    """Initialize Qdrant collection, handling dimension migrations."""
    collections = qdrant_client.get_collections().collections
    collection_names = [c.name for c in collections]

    if settings.qdrant_collection not in collection_names:
        qdrant_client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=settings.embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )
        logger.info(
            "Created Qdrant collection '%s' with %d dimensions",
            settings.qdrant_collection,
            settings.embedding_dimensions,
        )
        return

    # Collection exists — verify dimension compatibility
    existing = qdrant_client.get_collection(settings.qdrant_collection)
    vector_report = describe_vectors(existing.config.params.vectors)
    if not is_legacy_compatible(vector_report, settings.embedding_dimensions):
        raise RuntimeError(
            f"Qdrant collection '{settings.qdrant_collection}' is incompatible: "
            f"expected one unnamed {settings.embedding_dimensions}-dimensional "
            "Cosine vector; found "
            f"{vector_report}. "
            "No collection changes were made."
        )
    existing_size = vector_report["dimensions"]
    logger.info(
        "Qdrant collection '%s' ready (%d dimensions)",
        settings.qdrant_collection,
        existing_size,
    )


def get_qdrant():
    return qdrant_client
