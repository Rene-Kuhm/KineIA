"""Host-safe, explicit hybrid backfill and read-only verification CLI."""

import argparse
import json
import os
import sys
from pathlib import Path

from qdrant_client import QdrantClient

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.config import Settings
from app.core.rag.sparse_encoder import SpanishBm25Encoder
from app.db.hybrid_backfill import backfill_hybrid, verify_hybrid
from app.db.hybrid_readiness import (
    AttestationError,
    create_attestation,
    write_attestation,
)


class SafeParser(argparse.ArgumentParser):
    def error(self, _message):
        raise AttestationError("invalid_arguments")
def offset(value: str):
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value
def parser() -> argparse.ArgumentParser:
    result = SafeParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True, parser_class=SafeParser)
    for name in ("backfill", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--page-size", type=int, default=100)
    backfill = commands.choices["backfill"]
    backfill.add_argument("--offset", type=offset)
    backfill.add_argument("--max-pages", type=int)
    verify = commands.choices["verify"]
    verify.add_argument("--attestation-out", type=Path)
    verify.add_argument("--attestation-ttl-seconds", type=int, default=900)
    return result
def main(argv: list[str] | None = None) -> int:
    try:
        operation = argv[0] if argv and argv[0] in ("backfill", "verify") else "unknown"
        args = parser().parse_args(argv)
        operation = args.command
        settings = Settings(_env_file=Path(__file__).parents[2] / ".env")
        client = QdrantClient(url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"),
                              check_compatibility=False)
        common = dict(client=client, legacy=settings.qdrant_collection,
                      hybrid=settings.qdrant_hybrid_collection,
                      dense_name=settings.qdrant_dense_vector_name,
                      sparse_name=settings.qdrant_sparse_vector_name,
                      dimensions=settings.embedding_dimensions, page_size=args.page_size)
        version_text = client.info().version
        version = tuple(int(part) for part in version_text.split(".")[:2])
        if version < (1, 18):
            raise RuntimeError("unsupported Qdrant version")
        if args.command == "backfill":
            report = backfill_hybrid(**common, encoder=SpanishBm25Encoder(),
                                     offset=args.offset, max_pages=args.max_pages)
            exit_code = 1 if report["errors"] else 0
        else:
            report = verify_hybrid(**common)
            exit_code = 0 if report["ready"] else 1
            if args.attestation_out:
                artifact = create_attestation(
                    report=report, legacy=common["legacy"], hybrid=common["hybrid"],
                    qdrant_version=version_text, dense_name=common["dense_name"],
                    sparse_name=common["sparse_name"], dimensions=common["dimensions"],
                    secret=os.getenv("HYBRID_READINESS_HMAC_KEY", ""),
                    ttl_seconds=args.attestation_ttl_seconds,
                )
                write_attestation(args.attestation_out, artifact)
                print(json.dumps({"operation": "verify", "status": "attested"},
                                 sort_keys=True))
                return 0
        print(json.dumps({"operation": args.command} | report, sort_keys=True))
        return exit_code
    except AttestationError as error:
        print(json.dumps({"operation": operation, "status": "error",
                          "reason": error.reason}, sort_keys=True))
        return 1 if error.reason == "verification_not_ready" else 2
    except Exception:
        print(json.dumps({"operation": operation, "status": "error",
                          "reason": "migration_failed"}, sort_keys=True))
        return 2
if __name__ == "__main__":
    raise SystemExit(main())
