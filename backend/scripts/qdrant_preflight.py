"""Read-only Qdrant compatibility inventory for the legacy collection."""

import json
import os
import sys
from pathlib import Path

from qdrant_client import QdrantClient

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.config import settings
from app.db.qdrant_preflight import run_preflight


def main() -> int:
    client = QdrantClient(
        url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"),
        check_compatibility=False,
    )
    report, exit_code = run_preflight(
        client,
        settings.qdrant_collection,
        settings.embedding_dimensions,
    )
    print(json.dumps(report, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
