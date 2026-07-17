#!/usr/bin/env python3
# ruff: noqa: E501, E302
"""Strict, offline retrieval benchmark harness. No production policy decisions."""

import argparse
import hashlib
import inspect
import json
import math
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

MAX_BYTES, MAX_CASES, MAX_RELEVANCE, MAX_CHUNKS = 2_000_000, 1_000, 100, 50_000
TOP_K = 20
LOCALES = {"es-AR"}
CATEGORIES = {"canonical", "misspelled", "ambiguous", "unanswerable", "red_flag"}
ACTIONS = {"answer", "clarify", "abstain", "urgent_redirect"}
CASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}\Z")
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
PHI_FIELDS = {"patient_name", "patient_id", "medical_record_number", "mrn", "email", "phone", "address", "date_of_birth", "dob", "user_id", "history", "fragment"}

class BenchmarkError(ValueError):
    pass

def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"

def _digest(value):
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()

def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BenchmarkError("duplicate_key")
        result[key] = value
    return result

def _load(path):
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise BenchmarkError("file_too_large")
    data = path.read_bytes()
    if len(data) > MAX_BYTES:
        raise BenchmarkError("file_too_large")
    try:
        return json.loads(data, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BenchmarkError("invalid_json") from error

def _object(value, allowed, required=None):
    if type(value) is not dict:
        raise BenchmarkError("object_required")
    keys = set(value)
    required = allowed if required is None else required
    if keys & PHI_FIELDS or keys - set(allowed) or set(required) - keys:
        raise BenchmarkError("invalid_fields")

def _string(value, maximum=4000):
    if type(value) is not str or not value or len(value) > maximum:
        raise BenchmarkError("invalid_string")

def _identifier(value, maximum):
    _string(value, maximum)
    if not SAFE_ID.fullmatch(value):
        raise BenchmarkError("invalid_identifier")

def _utc(value):
    _string(value, 40)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
        raise BenchmarkError("invalid_timestamp")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise BenchmarkError("invalid_timestamp") from error

def _identity(value, *, grade=False):
    fields = {"source_id", "source_version_id", "chunk_index"} | ({"grade"} if grade else set())
    _object(value, fields)
    _string(value["source_id"], 200)
    _string(value["source_version_id"], 200)
    if type(value["chunk_index"]) is not int or value["chunk_index"] < 0:
        raise BenchmarkError("invalid_chunk_index")
    if grade and (type(value["grade"]) is not int or value["grade"] not in range(4)):
        raise BenchmarkError("invalid_grade")
    return value["source_id"], value["source_version_id"], value["chunk_index"]

def _validate_inventory(value):
    _object(value, {"schema_version", "chunks"})
    if value["schema_version"] != "kineia.corpus-inventory.v1" or type(value["chunks"]) is not list:
        raise BenchmarkError("invalid_inventory")
    if not value["chunks"] or len(value["chunks"]) > MAX_CHUNKS:
        raise BenchmarkError("invalid_inventory_size")
    identities = [_identity(chunk) for chunk in value["chunks"]]
    if len(identities) != len(set(identities)):
        raise BenchmarkError("duplicate_inventory_identity")
    return set(identities)

def _validate_validation(value):
    _object(value, {"status", "reviewers", "reviewed_at", "consensus_id"})
    status = value["status"]
    _string(status, 20)
    if status not in {"draft", "expert_validated"} or type(value["reviewers"]) is not list:
        raise BenchmarkError("invalid_validation")
    if status == "draft":
        if value != {"status": "draft", "reviewers": [], "reviewed_at": None, "consensus_id": None}:
            raise BenchmarkError("invalid_draft")
        return
    for reviewer in value["reviewers"]:
        _identifier(reviewer, 100)
    if len(value["reviewers"]) < 2 or len(set(value["reviewers"])) != len(value["reviewers"]):
        raise BenchmarkError("invalid_reviewers")
    _utc(value["reviewed_at"])
    _identifier(value["consensus_id"], 200)

def _validate_benchmark(value, inventory):
    _object(value, {"schema_version", "cases"})
    if value["schema_version"] != "kineia.retrieval-benchmark.v1" or type(value["cases"]) is not list:
        raise BenchmarkError("invalid_benchmark")
    if not value["cases"] or len(value["cases"]) > MAX_CASES:
        raise BenchmarkError("invalid_case_count")
    case_ids = set()
    allowed = {"case_id", "locale", "category", "query", "filters", "relevant", "expected_action", "validation"}
    for case in value["cases"]:
        _object(case, allowed)
        for field in ("case_id", "locale", "category", "query", "expected_action"):
            _string(case[field])
        if not CASE_ID.fullmatch(case["case_id"]) or case["case_id"] in case_ids or case["locale"] not in LOCALES:
            raise BenchmarkError("invalid_case_identity")
        case_ids.add(case["case_id"])
        if case["category"] not in CATEGORIES or case["expected_action"] not in ACTIONS:
            raise BenchmarkError("invalid_case_enum")
        _object(case["filters"], {"area", "evidence_level"}, set())
        for value in case["filters"].values():
            _string(value, 100)
        if type(case["relevant"]) is not list or len(case["relevant"]) > MAX_RELEVANCE or case["expected_action"] == "answer" and not any(item.get("grade", 0) for item in case["relevant"] if type(item) is dict):
            raise BenchmarkError("invalid_relevance")
        relevant = [_identity(item, grade=True) for item in case["relevant"]]
        if len(relevant) != len(set(relevant)) or any(item not in inventory for item in relevant):
            raise BenchmarkError("invalid_relevance_identity")
        _validate_validation(case["validation"])

def load_inputs(benchmark_path, inventory_path):
    benchmark, inventory = _load(benchmark_path), _load(inventory_path)
    identities = _validate_inventory(inventory)
    _validate_benchmark(benchmark, identities)
    return benchmark, inventory

def _ranked_identities(documents, inventory):
    result, seen = [], set()
    for document in documents[:TOP_K]:
        metadata = document.get("metadata", {}) if type(document) is dict else {}
        identity = (metadata.get("source_id"), metadata.get("source_version_id"), metadata.get("chunk_index"))
        valid = type(identity[0]) is str and type(identity[1]) is str and type(identity[2]) is int and identity in inventory and identity not in seen
        result.append(identity if valid else None)
        if valid:
            seen.add(identity)
    return result

def _case_metrics(relevance, ranked):
    graded = {identity: grade for identity, grade in relevance.items() if grade > 0}
    if not graded:
        return {name: None for name in ("hit_at_20", "recall_at_20", "mrr_at_20", "ndcg_at_20")}
    ranks = [index for index, identity in enumerate(ranked, 1) if identity in graded]
    dcg = sum(graded[identity] / math.log2(index + 1) for index, identity in enumerate(ranked, 1) if identity in graded)
    ideal = sum(grade / math.log2(index + 1) for index, grade in enumerate(sorted(graded.values(), reverse=True), 1))
    return {"hit_at_20": float(bool(ranks)), "recall_at_20": len(ranks) / len(graded),
            "mrr_at_20": 1 / ranks[0] if ranks else 0.0, "ndcg_at_20": dcg / ideal}

def _mean(values):
    values = [value for value in values if value is not None]
    return sum(values) / len(values) if values else None

def _aggregate(cases, rows, stage):
    selected = [(case, row) for case, row in zip(cases, rows) if case["validation"]["status"] == "expert_validated"]
    metrics = {name: _mean([row[stage][name] for _, row in selected]) for name in ("hit_at_20", "recall_at_20", "mrr_at_20", "ndcg_at_20")}
    answerable = [(case, row) for case, row in selected if case["expected_action"] == "answer"]
    metrics["coverage"] = _mean([row[stage]["hit_at_20"] for _, row in answerable]) if answerable else None
    return metrics

def _runtime_manifest(retriever, rerank_fn):
    root = Path(__file__).parents[1]
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise BenchmarkError("invalid_git_sha")
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root))
    identity = retriever.evaluation_identity()
    reranker_path = Path(inspect.getsourcefile(rerank_fn)).resolve()
    paths = {Path(__file__).resolve(), Path(inspect.getsourcefile(type(retriever))).resolve(), reranker_path}
    sources = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    models = {"embedding": identity["embedding_model"], "reranker_source": sources[reranker_path.relative_to(root).as_posix()]}
    return {"git_sha": sha, "git_dirty": dirty, "code_digest": _digest(sources), "model_digest": _digest(models), "config_digest": _digest(identity), "runtime_identity": identity}

def evaluate(benchmark, inventory, retriever, rerank_fn, *, timestamp):
    inventory_ids = _validate_inventory(inventory)
    _validate_benchmark(benchmark, inventory_ids)
    _utc(timestamp)
    rows, observed_modes, observed_scores, candidate_count = [], set(), set(), 0
    for case in benchmark["cases"]:
        filters = case["filters"]
        documents = retriever.search(query=case["query"], area=filters.get("area"),
                                     evidence_level=filters.get("evidence_level"), limit=TOP_K)
        candidate_count += len(documents)
        reranked = rerank_fn(query=case["query"], documents=documents, top_k=TOP_K)
        for document in documents:
            if type(document) is dict:
                if type(document.get("retrieval_mode")) is str:
                    observed_modes.add(document["retrieval_mode"])
                if type(document.get("score_type")) is str:
                    observed_scores.add(document["score_type"])
        relevance = {_identity(item, grade=True): item["grade"] for item in case["relevant"]}
        rows.append({"case_id": case["case_id"], "validation_status": case["validation"]["status"],
                     "retrieval": _case_metrics(relevance, _ranked_identities(documents, inventory_ids)),
                     "rerank": _case_metrics(relevance, _ranked_identities(reranked, inventory_ids))})
    expert = [case for case in benchmark["cases"] if case["validation"]["status"] == "expert_validated"]
    metrics = {stage: _aggregate(benchmark["cases"], rows, stage) for stage in ("retrieval", "rerank")}
    metrics.update({name: None for name in ("action_accuracy", "response_coverage", "correct_abstention", "clarification_accuracy", "critical_sensitivity", "critical_false_positive_rate", "citation_precision", "unsupported_answer_rate")})
    provenance = "no_results" if not candidate_count else "observed" if observed_modes and observed_scores else "unobserved"
    full_manifest = dict(_runtime_manifest(retriever, rerank_fn), benchmark_hash=_digest(benchmark), corpus_digest=_digest(inventory),
                         filters_digest=_digest([case["filters"] for case in benchmark["cases"]]),
                         observed_retrieval_modes=sorted(observed_modes), observed_score_types=sorted(observed_scores),
                         stages_executed=["retrieval", "rerank"], observed_candidate_count=candidate_count,
                         provenance_status=provenance, top_k=TOP_K, timestamp=timestamp)
    return {"schema_version": "kineia.retrieval-report.v1",
            "publishable": bool(expert) and len(expert) == len(benchmark["cases"]),
            "clinical_case_count": len(expert), "draft_case_count": len(benchmark["cases"]) - len(expert),
            "manifest": full_manifest, "cases": rows, "metrics": metrics}

class _Parser(argparse.ArgumentParser):
    def error(self, _message):
        raise BenchmarkError("invalid_arguments")

def main(argv=None):
    parser = _Parser()
    for name in ("benchmark", "inventory", "output"):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--timestamp")
    try:
        args = parser.parse_args(argv)
        benchmark, inventory = load_inputs(args.benchmark, args.inventory)
        backend = Path(__file__).resolve().parents[1] / "backend"
        sys.path.insert(0, str(backend))
        from app.core.rag.reranker import rerank
        from app.services.rag.retriever import retriever
        timestamp = args.timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        report = evaluate(benchmark, inventory, retriever, rerank, timestamp=timestamp)
        _atomic_write(args.output, canonical_json(report))
        return 0
    except Exception as error:
        code = "INVALID_INPUT" if isinstance(error, BenchmarkError) else "EVALUATION_FAILED"
        sys.stderr.write(canonical_json({"error": {"code": code}}))
        return 2

def _atomic_write(path, content):
    target = Path(path)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)

if __name__ == "__main__":
    raise SystemExit(main())
