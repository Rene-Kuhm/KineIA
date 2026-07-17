from dataclasses import dataclass
from datetime import datetime, timezone

from app.db.hybrid_collection import hybrid_collection_is_compatible
from app.db.hybrid_readiness import MAX_ARTIFACT_BYTES, AttestationError, validate_attestation


@dataclass(frozen=True)
class HybridGate:
    expires_at: datetime | None = None
    reason: str = "disabled"

    def allows_hybrid(self, now: datetime | None = None) -> bool:
        return self.expires_at is not None and (now or datetime.now(timezone.utc)) < self.expires_at
def _major_minor(version):
    return ".".join(str(int(part)) for part in version.split(".")[:2])
def _read_bounded(path):
    with path.open("rb") as handle:
        return handle.read(MAX_ARTIFACT_BYTES + 1)
def build_hybrid_gate(config, client, *, now: datetime | None = None) -> HybridGate:
    try:
        if config.qdrant_write_mode != "dual":
            raise AttestationError("write_mode_invalid")
        if config.hybrid_readiness_path is None:
            raise AttestationError("artifact_unavailable")
        artifact = validate_attestation(
            _read_bounded(config.hybrid_readiness_path),
            secret=config.hybrid_readiness_hmac_key.get_secret_value(), now=now,
        )
        legacy, hybrid = config.qdrant_collection, config.qdrant_hybrid_collection
        expected = {
            "legacy_collection": legacy, "hybrid_collection": hybrid,
            "dense_vector_name": config.qdrant_dense_vector_name,
            "sparse_vector_name": config.qdrant_sparse_vector_name,
            "dimensions": config.embedding_dimensions,
        }
        if any(artifact[key] != value for key, value in expected.items()):
            raise AttestationError("configuration_mismatch")
        if _major_minor(client.info().version) != artifact["qdrant_compatibility"]:
            raise AttestationError("qdrant_mismatch")
        compatible = hybrid_collection_is_compatible(
            client, collection_name=config.qdrant_hybrid_collection,
            dense_name=config.qdrant_dense_vector_name,
            sparse_name=config.qdrant_sparse_vector_name,
            dimensions=config.embedding_dimensions,
        )
        if not compatible:
            raise AttestationError("schema_mismatch")
        counts = [client.count(collection_name=name, exact=True).count for name in (legacy, hybrid)]
        if counts != [artifact["legacy_count"], artifact["hybrid_count"]]:
            raise AttestationError("count_mismatch")
        expires = datetime.fromisoformat(artifact["expires_at"].replace("Z", "+00:00"))
        return HybridGate(expires, "ready")
    except AttestationError as error:
        return HybridGate(reason=error.reason)
    except OSError:
        return HybridGate(reason="artifact_unavailable")
    except Exception:
        return HybridGate(reason="runtime_check_failed")
