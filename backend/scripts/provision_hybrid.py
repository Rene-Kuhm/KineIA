"""Explicit host command for non-destructive hybrid collection provisioning."""

import json
import os
import sys
from pathlib import Path

from qdrant_client import QdrantClient

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.config import Settings
from app.db.hybrid_collection import provision_hybrid_collection

settings = Settings(_env_file=Path(__file__).parents[2] / ".env")


def main() -> int:
    client = QdrantClient(
        url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"),
        check_compatibility=False,
    )
    report, exit_code = provision_hybrid_collection(
        client,
        legacy_collection_name=settings.qdrant_collection,
        collection_name=settings.qdrant_hybrid_collection,
        dense_vector_name=settings.qdrant_dense_vector_name,
        sparse_vector_name=settings.qdrant_sparse_vector_name,
        dimensions=settings.embedding_dimensions,
    )
    print(json.dumps(report, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
