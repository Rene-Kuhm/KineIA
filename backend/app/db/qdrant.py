import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.config import settings

logger = logging.getLogger(__name__)

qdrant_client = QdrantClient(url=settings.qdrant_url)


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
    existing_size = existing.config.params.vectors.size

    if existing_size != settings.embedding_dimensions:
        logger.warning(
            "⚠️  Qdrant collection '%s' has %d dimensions but config expects %d. "
            "Upserts will FAIL. Run: docker compose exec backend python -c \""
            "from app.db.qdrant import qdrant_client; "
            "qdrant_client.delete_collection('%s'); "
            "print('Collection deleted. Restart to recreate.')\"",
            settings.qdrant_collection,
            existing_size,
            settings.embedding_dimensions,
            settings.qdrant_collection,
        )
    else:
        logger.info(
            "Qdrant collection '%s' ready (%d dimensions)",
            settings.qdrant_collection,
            existing_size,
        )


def get_qdrant():
    return qdrant_client
