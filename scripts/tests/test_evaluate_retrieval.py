# ruff: noqa: E501, I001, E301, E302, E306
import json
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.evaluate_retrieval import BenchmarkError, _atomic_write, canonical_json, evaluate, load_inputs, main  # noqa: I001
IDENTITY = {"source_id": "s1", "source_version_id": "v1", "chunk_index": 1}
def inventory():
    return {"schema_version": "kineia.corpus-inventory.v1", "chunks": [IDENTITY, {"source_id": "s1", "source_version_id": "v1", "chunk_index": 2}, {"source_id": "s2", "source_version_id": "v1", "chunk_index": 1}]}
def benchmark(status="expert_validated"):
    validation = {"status": status, "reviewers": ["k1", "k2"] if status != "draft" else [], "reviewed_at": "2026-07-17T12:00:00Z" if status != "draft" else None, "consensus_id": "review-1" if status != "draft" else None}
    return {"schema_version": "kineia.retrieval-benchmark.v1", "cases": [{
        "case_id": "case-1", "locale": "es-AR", "category": "canonical", "query": "PRIVATE QUERY", "filters": {"area": "PRIVATE FILTER"},
        "relevant": [dict(IDENTITY, grade=3), {"source_id": "s1", "source_version_id": "v1", "chunk_index": 2, "grade": 1}], "expected_action": "answer", "validation": validation,
    }]}
class FakeRetriever:
    def __init__(self, mode="hybrid", documents=None):
        self.calls, self.mode = [], mode
        self.documents = documents if documents is not None else [{"metadata": {"source_id": "s2", "source_version_id": "v1", "chunk_index": 1}, "retrieval_mode": "hybrid", "score_type": "rrf"}, {"metadata": IDENTITY, "retrieval_mode": "hybrid", "score_type": "rrf"}]
    def evaluation_identity(self):
        return {"class": "tests.FakeRetriever", "configured_read_mode": self.mode, "served_mode": self.mode, "score_type": "rrf" if self.mode == "hybrid" else "cosine", "embedding_model": "fake-embedding"}
    def search(self, **kwargs):
        self.calls.append(kwargs)
        return self.documents
def test_golden_metrics_and_private_output_contract(monkeypatch):
    monkeypatch.setattr("scripts.evaluate_retrieval.subprocess.check_output", lambda command, **_kwargs: "a" * 40 if "rev-parse" in command else b"dirty")
    retriever, rerank_calls = FakeRetriever(), []
    def rerank_fn(**kwargs):
        rerank_calls.append(kwargs)
        return [{"metadata": {"source_id": "s1", "source_version_id": "v1", "chunk_index": 2}}, {"metadata": {"source_id": "s1", "source_version_id": "v1", "chunk_index": 2}}, {"metadata": IDENTITY}]
    report = evaluate(benchmark(), inventory(), retriever, rerank_fn, timestamp="2026-07-17T12:00:00Z")
    retrieval, reranked = report["cases"][0]["retrieval"], report["cases"][0]["rerank"]
    assert retrieval == {"hit_at_20": 1.0, "recall_at_20": 0.5, "mrr_at_20": 0.5, "ndcg_at_20": pytest.approx(0.521296)}
    assert reranked["hit_at_20"] == reranked["recall_at_20"] == reranked["mrr_at_20"] == 1.0
    assert reranked["ndcg_at_20"] == pytest.approx(0.688529)
    assert retriever.calls[0]["limit"] == rerank_calls[0]["top_k"] == 20
    assert report["publishable"] is True and report["metrics"]["retrieval"]["coverage"] == 1.0 and report["manifest"]["observed_retrieval_modes"] == ["hybrid"] and report["manifest"]["observed_score_types"] == ["rrf"] and report["manifest"]["provenance_status"] == "observed" and report["manifest"]["git_dirty"] is True and len(report["manifest"]["git_sha"]) == 40 and len(report["manifest"]["code_digest"]) == 64
    assert {name for name, value in report["metrics"].items() if value is None} == {"action_accuracy", "response_coverage", "correct_abstention", "clarification_accuracy", "critical_sensitivity", "critical_false_positive_rate", "citation_precision", "unsupported_answer_rate"}
    encoded = canonical_json(report)
    assert "PRIVATE QUERY" not in encoded and "PRIVATE FILTER" not in encoded
@pytest.mark.parametrize("mutation", [lambda b, _i: b["cases"][0].update(patient_name="x"), lambda b, _i: b["cases"][0].update(case_id="../unsafe"), lambda b, _i: b["cases"][0].update(locale="es"), lambda b, _i: b["cases"][0]["relevant"][0].update(chunk_index=True), lambda b, _i: b["cases"][0]["relevant"].append(deepcopy(b["cases"][0]["relevant"][0])), lambda b, _i: b["cases"][0]["validation"].update(reviewers=["k1", " k2"]), lambda b, _i: b["cases"][0]["validation"].update(reviewers=["same", "same"]), lambda b, _i: b["cases"][0]["validation"].update(consensus_id="review-1 "), lambda b, _i: b["cases"][0]["validation"].update(reviewed_at="2026-07-17T12:00:00.1Z"), lambda b, i: i["chunks"].clear()])
def test_strict_schema_and_inventory_identity_validation(tmp_path, mutation):
    b, i = benchmark(), inventory()
    mutation(b, i)
    bp, ip = tmp_path / "b.json", tmp_path / "i.json"
    bp.write_text(json.dumps(b), encoding="utf-8")
    ip.write_text(json.dumps(i), encoding="utf-8")
    with pytest.raises(BenchmarkError):
        load_inputs(bp, ip)
    with pytest.raises(BenchmarkError):
        evaluate(b, i, FakeRetriever(), lambda **_kwargs: [], timestamp="2026-07-17T12:00:00Z")
def test_duplicate_keys_and_cli_errors_are_sanitized(tmp_path, capsys):
    secret = "PRIVATE-PATIENT-SENTINEL"
    bp, ip = tmp_path / "b.json", tmp_path / "i.json"
    bp.write_text('{"schema_version":"x","schema_version":"' + secret + '"}', encoding="utf-8")
    ip.write_text(json.dumps(inventory()), encoding="utf-8")
    with pytest.raises(BenchmarkError):
        load_inputs(bp, ip)
    invalid = benchmark()
    invalid["cases"][0]["category"] = []
    bp.write_text(json.dumps(invalid), encoding="utf-8")
    assert main(["--benchmark", str(bp), "--inventory", str(ip), "--output", str(tmp_path / "o")]) == 2
    assert capsys.readouterr().err == '{"error":{"code":"INVALID_INPUT"}}\n'
def test_draft_results_are_non_publishable_and_na():
    report = evaluate(benchmark("draft"), inventory(), FakeRetriever(documents=[]), lambda **_kwargs: [], timestamp="2026-07-17T12:00:00Z")
    other = evaluate(benchmark("draft"), inventory(), FakeRetriever("dense", []), lambda **_kwargs: [], timestamp="2026-07-17T12:00:00Z")
    assert report["publishable"] is False and report["metrics"]["retrieval"]["hit_at_20"] is None
    assert report["manifest"]["provenance_status"] == "no_results" and report["manifest"]["observed_candidate_count"] == 0 and report["manifest"]["observed_retrieval_modes"] == report["manifest"]["observed_score_types"] == [] and report["manifest"]["stages_executed"] == ["retrieval", "rerank"] and report["manifest"]["runtime_identity"]["served_mode"] == "hybrid" and report["manifest"]["runtime_identity"] != other["manifest"]["runtime_identity"] and report["manifest"]["config_digest"] != other["manifest"]["config_digest"]
def test_atomic_output_replaces_symlink_and_preserves_prior_on_failure(tmp_path, monkeypatch):
    target, referent = tmp_path / "report.json", tmp_path / "old.json"
    referent.write_text("old", encoding="utf-8")
    try:
        target.symlink_to(referent)
    except OSError:
        pytest.skip("symlinks unavailable")
    _atomic_write(target, "new")
    assert not target.is_symlink() and target.read_text(encoding="utf-8") == "new" and referent.read_text() == "old"
    target.write_text("prior", encoding="utf-8")
    monkeypatch.setattr(Path, "replace", lambda *_args: (_ for _ in ()).throw(OSError("replace")))
    with pytest.raises(OSError):
        _atomic_write(target, "lost")
    assert target.read_text() == "prior" and not list(tmp_path.glob(".*.tmp"))
