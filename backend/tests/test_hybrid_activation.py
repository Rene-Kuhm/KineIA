import logging
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from app.config import Settings
from app.db.hybrid_readiness import create_attestation
from qdrant_client.models import Fusion, SparseVector

NOW = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
SECRET = "h" * 32
def report():
    coverage = {"matched": 2, "total": 2, "percent": 100.0}
    return {
        "counts": {"legacy": 2, "v2": 2}, "id_digests": {"legacy": "id", "v2": "id"},
        "payload_digests": {"legacy": "payload", "v2": "payload"},
        "dense_coverage": coverage, "sparse_coverage": coverage.copy(),
        "ready": True, "missing_ids": [], "orphan_ids": [], "errors": [],
        "discrepancy_counts": {"missing": 0, "orphan": 0, "errors": 0},
        "truncated": {"missing_ids": False, "orphan_ids": False, "errors": False},
    }
def artifact(path, issued_at=NOW):
    path.write_bytes(create_attestation(report=report(), legacy="legacy", hybrid="hybrid",
        qdrant_version="1.18.2",
        dense_name="dense", sparse_name="sparse", dimensions=1024, secret=SECRET,
        issued_at=issued_at, ttl_seconds=900))
def config(path, **changes):
    values = dict(qdrant_collection="legacy", qdrant_hybrid_collection="hybrid",
                  qdrant_dense_vector_name="dense", qdrant_sparse_vector_name="sparse",
                  embedding_dimensions=1024, qdrant_write_mode="dual",
                  hybrid_readiness_path=path, hybrid_readiness_hmac_key=SECRET)
    values.update(changes)
    return Settings(_env_file=None, **values)
def test_valid_gate_uses_only_schema_and_exact_counts(tmp_path, monkeypatch):
    from app.services.rag import hybrid_gate as module
    artifact(path := tmp_path / "ready.json")
    client = MagicMock(info=lambda: SimpleNamespace(version="1.18.2"))
    client.count.side_effect = [SimpleNamespace(count=2), SimpleNamespace(count=2)]
    monkeypatch.setattr(module, "hybrid_collection_is_compatible", lambda *_args, **_kw: True)
    gate = module.build_hybrid_gate(config(path), client, now=NOW)
    assert gate.allows_hybrid(NOW) and all(c.kwargs["exact"] for c in client.count.call_args_list)
    client.scroll.assert_not_called()
@pytest.mark.parametrize(("kind", "changes", "now", "reason"), [
    ("missing", {}, NOW, "artifact_unavailable"), ("oversize", {}, NOW, "artifact_too_large"),
    ("tamper", {}, NOW, "signature_invalid"), ("future", {}, NOW, "artifact_not_yet_valid"),
    ("expired", {}, NOW + timedelta(seconds=901), "artifact_expired"),
    ("config", {"qdrant_hybrid_collection": "other"}, NOW, "configuration_mismatch"),
    ("count", {}, NOW, "count_mismatch"), ("schema", {}, NOW, "schema_mismatch"),
    ("legacy", {"qdrant_write_mode": "legacy"}, NOW, "write_mode_invalid"),
])
def test_invalid_startup_evidence_fails_closed(kind, changes, now, reason, tmp_path, monkeypatch):
    from app.services.rag import hybrid_gate as module
    path = tmp_path / "ready.json"
    if kind == "oversize":
        path.write_bytes(b"x" * 8193)
    elif kind != "missing":
        artifact(path, NOW + timedelta(seconds=61) if kind == "future" else NOW)
    if kind == "tamper":
        path.write_bytes(path.read_bytes().replace(b'"legacy_count":2', b'"legacy_count":3'))
    client = MagicMock(info=lambda: SimpleNamespace(version="1.18.2"))
    client.count.side_effect = [SimpleNamespace(count=2),
                                SimpleNamespace(count=1 if kind == "count" else 2)]
    monkeypatch.setattr(module, "hybrid_collection_is_compatible",
                        lambda *_args, **_kw: kind != "schema")
    assert module.build_hybrid_gate(config(path, **changes), client, now=now).reason == reason
def test_eligible_hybrid_serves_rrf_with_provenance(monkeypatch):
    from app.services.rag import retriever as module
    from app.services.rag.hybrid_gate import HybridGate
    point = MagicMock(score=0.75, payload={"text": "evidence", "area": "trauma"})
    client, encoder = MagicMock(), MagicMock()
    client.query_points.return_value = MagicMock(points=[point])
    encoder.encode.return_value = SparseVector(indices=[3], values=[0.7])
    monkeypatch.setattr(module, "SpanishBm25Encoder", lambda: encoder)
    monkeypatch.setattr(module, "generate_embedding", lambda _query: [0.1] * 1024)
    monkeypatch.setattr(module.settings, "qdrant_hybrid_collection", "hybrid")
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    gate = HybridGate(expires_at, "ready")
    assert gate.allows_hybrid(expires_at - timedelta(microseconds=1))
    assert not gate.allows_hybrid(expires_at)
    docs = module.Retriever(client=client, read_mode="hybrid", gate=gate).search("x", area="x")
    call = client.query_points.call_args.kwargs
    assert call["collection_name"] == "hybrid" and call["query"].fusion is Fusion.RRF
    assert all(item.filter is call["prefetch"][0].filter for item in call["prefetch"])
    assert (docs[0]["retrieval_mode"], docs[0]["score_type"]) == ("hybrid", "rrf")
def test_dense_and_expired_gate_never_initialize_sparse(monkeypatch):
    from app.services.rag import retriever as module
    from app.services.rag.hybrid_gate import HybridGate
    client, factory = MagicMock(), MagicMock()
    client.query_points.return_value = MagicMock(points=[MagicMock(payload={"text": "dense"})])
    monkeypatch.setattr(module, "SpanishBm25Encoder", factory)
    monkeypatch.setattr(module, "generate_embedding", lambda _query: [0.1])
    modes = [("dense", None, "dense"), ("hybrid", HybridGate(
        datetime.now(timezone.utc) - timedelta(seconds=1)), "dense_fallback")]
    for mode, gate, provenance in modes:
        result = module.Retriever(client=client, read_mode=mode, gate=gate).search("private")
        assert result[0]["retrieval_mode"] == provenance
    factory.assert_not_called()
def test_hybrid_failure_runs_one_fresh_dense_fallback_without_private_logs(monkeypatch):
    from app.services.rag import retriever as module
    from app.services.rag.hybrid_gate import HybridGate
    fallback = MagicMock(points=[MagicMock(score=0.5, payload={"text": "dense"})])
    client, encoder = MagicMock(), MagicMock()
    client.query_points.side_effect = [RuntimeError("PRIVATE"), fallback]
    encoder.encode.return_value = SparseVector(indices=[1], values=[1.0])
    monkeypatch.setattr(module, "SpanishBm25Encoder", lambda: encoder)
    monkeypatch.setattr(module, "generate_embedding", lambda _query: [0.1])
    monkeypatch.setattr(module.logger, "handlers", [handler := logging.Handler()])
    handler.emit = MagicMock(side_effect=RuntimeError)
    gate = HybridGate(datetime.now(timezone.utc) + timedelta(minutes=1), "ready")
    retriever = module.Retriever(client=client, read_mode="hybrid", gate=gate)
    result = retriever.search("PRIVATE", area="PRIVATE")
    assert client.query_points.call_count == 2 and result[0]["retrieval_mode"] == "dense_fallback"
    assert "PRIVATE" not in handler.emit.call_args.args[0].getMessage()
    client.query_points.side_effect = [RuntimeError("hybrid"), RuntimeError("dense-visible")]
    with pytest.raises(RuntimeError, match="dense-visible"):
        retriever.search("query")
@pytest.mark.asyncio
async def test_startup_dense_skips_gate_and_invalid_hybrid_does_not_block(tmp_path, monkeypatch):
    from app import main as module
    from app.services.rag.hybrid_gate import HybridGate
    builder = MagicMock(return_value=HybridGate(reason="signature_invalid"))
    monkeypatch.setattr(module, "build_hybrid_gate", builder, raising=False)
    client = MagicMock()
    path = tmp_path / "missing"
    dense = await module.create_retriever(config(path, retriever_read_mode="dense"), client)
    builder.assert_not_called()
    monkeypatch.setattr(module.logger, "handlers", [handler := logging.Handler()])
    handler.emit = MagicMock(side_effect=RuntimeError)
    hybrid = await module.create_retriever(config(path, retriever_read_mode="hybrid"), client)
    assert (handler.emit.call_count, dense.read_mode, hybrid.read_mode, hybrid.gate.reason) == (
        1, "dense", "hybrid", "signature_invalid")
