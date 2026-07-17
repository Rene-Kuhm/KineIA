import hashlib
import hmac
import json
import os
import tempfile
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA_VERSION, MAX_ARTIFACT_BYTES = 1, 8192
MIN_TTL_SECONDS, MAX_TTL_SECONDS, MAX_FUTURE_SKEW_SECONDS = 60, 86400, 60
_IS_WINDOWS = os.name == "nt"
_REPORT_FIELDS = set(("counts id_digests payload_digests dense_coverage sparse_coverage "
                      "missing_ids orphan_ids errors discrepancy_counts truncated ready").split())
_FIELDS = set(("schema_version issued_at expires_at legacy_collection hybrid_collection "
               "qdrant_compatibility dense_vector_name sparse_vector_name dimensions legacy_count "
               "hybrid_count legacy_id_digest hybrid_id_digest legacy_payload_digest "
               "hybrid_payload_digest dense_coverage_matched dense_coverage_total "
               "dense_coverage_percent sparse_coverage_matched sparse_coverage_total "
               "sparse_coverage_percent signature").split())
class AttestationError(ValueError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)
def _reject(condition, reason):
    if condition:
        raise AttestationError(reason)
def _key(secret: str) -> bytes:
    _reject(not isinstance(secret, str) or len(secret.encode()) < 32, "secret_too_short")
    return secret.encode()
def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"),
                      sort_keys=True).encode() + b"\n"
def _timestamp(value: datetime) -> str:
    _reject(value.tzinfo is None or value.utcoffset() != timedelta(0), "timestamp_invalid")
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
def _parse_timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if value == _timestamp(parsed):
            return parsed
    except (AttributeError, TypeError, ValueError, AttestationError):
        pass
    raise AttestationError("timestamp_invalid") from None
def _ready(report: dict) -> None:
    _reject(not isinstance(report, dict) or set(report) != _REPORT_FIELDS, "verification_invalid")
    _reject(report.get("ready") is not True, "verification_not_ready")
    counts, flags = report.get("counts"), report.get("truncated")
    dense, sparse = report.get("dense_coverage"), report.get("sparse_coverage")
    _reject(not isinstance(counts, dict) or set(counts) != {"legacy", "v2"},
            "verification_invalid")
    count = counts.get("legacy")
    def coverage_ok(item):
        return (isinstance(item, dict) and set(item) == {"matched", "total", "percent"}
                and type(item["matched"]) is int and type(item["total"]) is int
                and type(item["percent"]) is float
                and item == {"matched": count, "total": count, "percent": 100.0})
    digests = (report.get("id_digests"), report.get("payload_digests"))
    _reject(not all(type(v) is int for v in counts.values()) or count < 1 or counts["v2"] != count
            or not coverage_ok(dense) or not coverage_ok(sparse)
            or any(not isinstance(item, dict) or set(item) != {"legacy", "v2"}
                   or not isinstance(item["legacy"], str) or not item["legacy"]
                   or item["legacy"] != item["v2"] for item in digests)
            or any(report.get(key) != [] for key in ("missing_ids", "orphan_ids", "errors"))
            or report.get("discrepancy_counts") != {"missing": 0, "orphan": 0, "errors": 0}
            or any(type(value) is not int for value in report["discrepancy_counts"].values())
            or flags != {"missing_ids": False, "orphan_ids": False, "errors": False}
            or any(type(value) is not bool for value in flags.values()), "verification_invalid")
def create_attestation(*, report: dict, legacy: str, hybrid: str, qdrant_version: str,
                       dense_name: str, sparse_name: str, dimensions: int, secret: str,
                       issued_at: datetime | None = None, ttl_seconds: int = 900) -> bytes:
    _ready(report)
    key = _key(secret)
    _reject(type(ttl_seconds) is not int or not MIN_TTL_SECONDS <= ttl_seconds <= MAX_TTL_SECONDS,
            "ttl_invalid")
    _reject(not all(isinstance(value, str) and value and len(value) <= 255
                    for value in (legacy, hybrid, dense_name, sparse_name)) or legacy == hybrid
            or type(dimensions) is not int or dimensions < 1, "configuration_invalid")
    try:
        version = ".".join(str(int(part)) for part in qdrant_version.split(".")[:2])
        _reject(tuple(map(int, version.split("."))) < (1, 18), "qdrant_incompatible")
    except (AttributeError, TypeError, ValueError, AttestationError):
        raise AttestationError("qdrant_incompatible") from None
    now = issued_at or datetime.now(timezone.utc)
    counts, ids, payloads = report["counts"], report["id_digests"], report["payload_digests"]
    dense, sparse = report["dense_coverage"], report["sparse_coverage"]
    body = {
        "schema_version": SCHEMA_VERSION, "issued_at": _timestamp(now),
        "expires_at": _timestamp(now + timedelta(seconds=ttl_seconds)), "legacy_collection": legacy,
        "hybrid_collection": hybrid,
        "qdrant_compatibility": version, "dense_vector_name": dense_name,
        "sparse_vector_name": sparse_name, "dimensions": dimensions,
        "legacy_count": counts["legacy"], "hybrid_count": counts["v2"],
        "legacy_id_digest": ids["legacy"], "hybrid_id_digest": ids["v2"],
        "legacy_payload_digest": payloads["legacy"], "hybrid_payload_digest": payloads["v2"],
        "dense_coverage_matched": dense["matched"], "dense_coverage_total": dense["total"],
        "dense_coverage_percent": dense["percent"], "sparse_coverage_matched": sparse["matched"],
        "sparse_coverage_total": sparse["total"], "sparse_coverage_percent": sparse["percent"],
    }
    body["signature"] = hmac.new(key, _canonical(body), hashlib.sha256).hexdigest()
    artifact = _canonical(body)
    _reject(len(artifact) > MAX_ARTIFACT_BYTES, "artifact_too_large")
    return artifact
def _pairs(items):
    result = dict(items)
    _reject(len(result) != len(items), "artifact_duplicate_key")
    return result
def _schema_valid(value: dict) -> bool:
    count, other = value.get("legacy_count"), value.get("hybrid_count")
    strings = ("legacy_collection", "hybrid_collection", "dense_vector_name",
               "sparse_vector_name", "legacy_id_digest", "hybrid_id_digest",
               "legacy_payload_digest", "hybrid_payload_digest")
    try:
        version = tuple(map(int, value["qdrant_compatibility"].split(".")))
    except (AttributeError, TypeError, ValueError):
        return False
    return (type(value.get("schema_version")) is int and value["schema_version"] == SCHEMA_VERSION
        and all(isinstance(value.get(field), str) and value[field] for field in strings)
        and value["legacy_collection"] != value["hybrid_collection"]
        and len(version) == 2 and version >= (1, 18)
        and type(value.get("dimensions")) is int and value["dimensions"] > 0
        and type(count) is type(other) is int and count > 0 and other == count
        and value["legacy_id_digest"] == value["hybrid_id_digest"]
        and value["legacy_payload_digest"] == value["hybrid_payload_digest"]
        and all(type(value.get(f"{kind}_coverage_matched")) is int
                and type(value.get(f"{kind}_coverage_total")) is int
                and type(value.get(f"{kind}_coverage_percent")) is float
                and value[f"{kind}_coverage_matched"] == count
                and value[f"{kind}_coverage_total"] == count
                and value[f"{kind}_coverage_percent"] == 100.0
                for kind in ("dense", "sparse")))
def validate_attestation(data: bytes, *, secret: str, now: datetime | None = None) -> dict:
    key = _key(secret)
    _reject(not isinstance(data, bytes) or len(data) > MAX_ARTIFACT_BYTES, "artifact_too_large")
    try:
        artifact = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise AttestationError("artifact_invalid_json") from None
    _reject(not isinstance(artifact, dict) or set(artifact) != _FIELDS, "artifact_schema_invalid")
    _reject(data != _canonical(artifact), "artifact_noncanonical")
    signature = artifact.pop("signature")
    valid_hex = (isinstance(signature, str) and len(signature) == 64 and signature.isascii()
                 and all(character in "0123456789abcdef" for character in signature))
    expected = hmac.new(key, _canonical(artifact), hashlib.sha256).hexdigest()
    _reject(not valid_hex or not hmac.compare_digest(signature, expected), "signature_invalid")
    _reject(not _schema_valid(artifact), "artifact_schema_invalid")
    issued, expires = map(_parse_timestamp, (artifact["issued_at"], artifact["expires_at"]))
    current = now or datetime.now(timezone.utc)
    _timestamp(current)
    _reject(issued > current + timedelta(seconds=MAX_FUTURE_SKEW_SECONDS),
            "artifact_not_yet_valid")
    _reject(expires <= current, "artifact_expired")
    _reject(issued.utcoffset() != timedelta(0) or expires.utcoffset() != timedelta(0)
            or not MIN_TTL_SECONDS <= (expires - issued).total_seconds() <= MAX_TTL_SECONDS,
            "timestamp_invalid")
    return artifact | {"signature": signature}
def _move_file_ex(source, target, flags):
    import ctypes
    return ctypes.windll.kernel32.MoveFileExW(str(source), str(target), flags)
def _windows_replace(source, target) -> None:
    _reject(not _move_file_ex(source, target, 0x9), "write_failed")
def _open_directory(path):
    return os.open(path, os.O_RDONLY)
def _durable_replace(source, target) -> None:
    if _IS_WINDOWS:
        return _windows_replace(source, target)
    descriptor = _open_directory(target.parent)
    try:
        os.replace(source, target)
        try:
            os.fsync(descriptor)
        except OSError:
            raise AttestationError("write_durability_unknown") from None
    finally:
        with suppress(OSError):
            os.close(descriptor)
def write_attestation(path: Path, artifact: bytes) -> None:
    target, temporary = Path(path), None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(artifact)
            handle.flush()
            os.fsync(handle.fileno())
        with suppress(OSError):
            os.chmod(temporary, 0o600)
        _durable_replace(temporary, target)
        temporary = None
        with suppress(OSError):
            os.chmod(target, 0o600)
    except OSError:
        raise AttestationError("write_failed") from None
    finally:
        if temporary:
            with suppress(OSError):
                os.unlink(temporary)
