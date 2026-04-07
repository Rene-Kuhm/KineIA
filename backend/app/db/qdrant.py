from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.config import settings

qdrant_client = QdrantClient(url=settings.qdrant_url)


async def init_qdrant_collection():
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


def get_qdrant():
    return qdrant_client
