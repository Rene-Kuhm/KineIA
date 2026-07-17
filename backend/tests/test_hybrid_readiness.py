import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from app.db import hybrid_readiness as module

from backend.scripts import hybrid_migration as cli

NOW = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
SECRET = "s" * 32
def ready_report():
    coverage = {"matched": 2, "total": 2, "percent": 100.0}
    return {
        "counts": {"legacy": 2, "v2": 2}, "id_digests": {"legacy": "id", "v2": "id"},
        "payload_digests": {"legacy": "payload", "v2": "payload"},
        "dense_coverage": coverage, "sparse_coverage": coverage.copy(),
        "missing_ids": [], "orphan_ids": [], "errors": [],
        "discrepancy_counts": {"missing": 0, "orphan": 0, "errors": 0},
        "truncated": {"missing_ids": False, "orphan_ids": False, "errors": False},
        "ready": True,
    }
def report(**changes):
    return ready_report() | changes
dump = module._canonical
def create(**changes):
    values = dict(report=ready_report(), legacy="legacy", hybrid="v2-20260717",
                  qdrant_version="1.18.2", dense_name="dense", sparse_name="sparse",
                  dimensions=1024, secret=SECRET, issued_at=NOW, ttl_seconds=900)
    values.update(changes)
    return module.create_attestation(**values)
def alter(signature=None, remove=None, **changes):
    value = json.loads(create())
    value.update(changes)
    value.pop(remove, None)
    value.pop("signature", None)
    value["signature"] = signature if signature is not None else module.hmac.new(
        SECRET.encode(), dump(value), module.hashlib.sha256).hexdigest()
    return dump(value)
def test_ready_report_round_trips_as_canonical_signed_artifact():
    artifact = create()
    module.validate_attestation(artifact, secret=SECRET, now=NOW)
    assert artifact == create() == dump(json.loads(artifact))
@pytest.mark.parametrize(("artifact", "reason"), [
    (lambda: create().replace(b'"legacy_count":2', b'"legacy_count":3'), "signature_invalid"),
    (lambda: alter(schema_version=True), "artifact_schema_invalid"),
    (lambda: alter(extra="field"), "artifact_schema_invalid"),
    (lambda: alter(dense_coverage_matched=2.0), "artifact_schema_invalid"),
    (lambda: alter(hybrid_count=2.0), "artifact_schema_invalid"),
    (lambda: alter(issued_at="2026-07-17T12:00:00+00:00"), "timestamp_invalid"),
    (lambda: alter(issued_at="2026-07-17T12:00:00.000Z"), "timestamp_invalid"),
    (lambda: alter(issued_at="2026-07-17T12:00:00"), "timestamp_invalid"),
    (lambda: b'{"schema_version":1,"schema_version":1}', "artifact_duplicate_key"),
    (lambda: b"x" * 8193, "artifact_too_large"),
    (lambda: json.dumps(json.loads(create()), indent=2).encode(), "artifact_noncanonical"),
    (lambda: alter("é" * 32), "signature_invalid"),
    (lambda: alter("A" * 64), "signature_invalid"),
    (lambda: alter("a" * 63), "signature_invalid"),
])
def test_validation_rejects_malformed_artifacts(artifact, reason):
    with pytest.raises(module.AttestationError, match=reason):
        module.validate_attestation(artifact(), secret=SECRET, now=NOW)
@pytest.mark.parametrize(("operation", "reason"), [
    (lambda: create(secret="x" * 31), "secret_too_short"),
    (lambda: create(ttl_seconds=86401), "ttl_invalid"),
    (lambda: create(report=report(ready=False)), "verification_not_ready"),
    (lambda: create(report=report(counts={"legacy": 2, "v2": 2.0})), "verification_invalid"),
    (lambda: create(report=report(counts={"legacy": True, "v2": True})), "verification_invalid"),
    (lambda: create(report=report(dense_coverage={
        "matched": 2.0, "total": 2, "percent": 100.0})), "verification_invalid"),
    (lambda: create(report=report(discrepancy_counts={
        "missing": 0.0, "orphan": 0, "errors": 0})), "verification_invalid"),
    (lambda: create(report=report(truncated={
        "missing_ids": 0, "orphan_ids": False, "errors": False})), "verification_invalid"),
    (lambda: module.validate_attestation(
        create(), secret=SECRET, now=NOW + timedelta(seconds=901)), "artifact_expired"),
    (lambda: module.validate_attestation(
        create(issued_at=NOW + timedelta(seconds=61)), secret=SECRET, now=NOW),
     "artifact_not_yet_valid"),
])
def test_creation_rejects_unsafe_inputs(operation, reason):
    with pytest.raises(module.AttestationError, match=reason):
        operation()
def test_write_failure_and_durability_contract(tmp_path, monkeypatch):
    path = tmp_path / "ready.json"
    monkeypatch.setattr(module.os, "chmod", lambda *_args: (_ for _ in ()).throw(OSError()))
    module.write_attestation(path, create())
    valid = path.read_bytes()
    with pytest.raises(module.AttestationError, match="verification_not_ready"):
        module.write_attestation(path, create(report=report(ready=False)))
    monkeypatch.setattr(module, "_IS_WINDOWS", True)
    monkeypatch.setattr(module, "_move_file_ex", lambda *_args: 0)
    with pytest.raises(module.AttestationError, match="write_failed"):
        module.write_attestation(path, create())
    monkeypatch.setattr(module, "_IS_WINDOWS", False)
    monkeypatch.setattr(module, "_open_directory", lambda *_args: (_ for _ in ()).throw(OSError()))
    with pytest.raises(module.AttestationError, match="write_failed"):
        module.write_attestation(path, create())
    assert path.read_bytes() == valid
    monkeypatch.setattr(module, "_open_directory", lambda *_args: 777)
    monkeypatch.setattr(module.os, "close", lambda *_args: None)
    monkeypatch.setattr(module.os, "fsync", lambda descriptor:
                        (_ for _ in ()).throw(OSError()) if descriptor == 777 else None)
    with pytest.raises(module.AttestationError, match="write_durability_unknown"):
        module.write_attestation(path, create())
    assert module.validate_attestation(path.read_bytes(), secret=SECRET, now=NOW)
    calls = []
    monkeypatch.setattr(module, "_IS_WINDOWS", True)
    monkeypatch.setattr(module, "_move_file_ex", lambda source, target, flags:
                        (calls.append(flags), module.os.replace(source, target), 1)[-1])
    module.write_attestation(path, create())
    assert path.read_bytes() == create() and calls == [0x9]
def cli_dependencies(monkeypatch):
    settings = SimpleNamespace(qdrant_collection="legacy", qdrant_hybrid_collection="v2-gen",
                               qdrant_dense_vector_name="dense", qdrant_sparse_vector_name="sparse",
                               embedding_dimensions=1024)
    monkeypatch.setattr(cli, "Settings", lambda **_kwargs: settings)
    monkeypatch.setattr(cli, "QdrantClient", lambda **_kwargs:
                        SimpleNamespace(info=lambda: SimpleNamespace(version="1.18.2")))
    monkeypatch.setattr(cli, "verify_hybrid", lambda **_kwargs: ready_report())
def test_verify_cli_writes_attestation_from_environment_secret(tmp_path, monkeypatch, capsys):
    cli_dependencies(monkeypatch)
    monkeypatch.setenv("HYBRID_READINESS_HMAC_KEY", SECRET)
    path = tmp_path / "ready.json"
    assert cli.main(["verify", "--attestation-out", str(path)]) == 0
    assert json.loads(capsys.readouterr().out) == {"operation": "verify", "status": "attested"}
    module.validate_attestation(path.read_bytes(), secret=SECRET)
    assert cli.main(["verify", "--attestation-out", str(path),
                     "--attestation-ttl-seconds", "59"]) == 2
    assert json.loads(capsys.readouterr().out)["reason"] == "ttl_invalid"
def test_cli_setup_failure_emits_one_sanitized_result(monkeypatch, capsys):
    monkeypatch.setattr(cli, "Settings", lambda **_kwargs:
                        (_ for _ in ()).throw(RuntimeError("secret")))
    assert cli.main(["verify"]) == 2
    assert capsys.readouterr().out.splitlines() == [
        '{"operation": "verify", "reason": "migration_failed", "status": "error"}']
def test_invalid_cli_arguments_are_non_echoing_json(capsys):
    for args in (["verify", "--unknown", "private-input"],
                 ["verify", "--attestation-ttl-seconds", "private-input"]):
        assert cli.main(args) == 2
        captured = capsys.readouterr()
        assert captured.err == "" and "private-input" not in captured.out
        assert json.loads(captured.out)["reason"] == "invalid_arguments"
