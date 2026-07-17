# Run the retrieval benchmark safely
Use `scripts/evaluate_retrieval.py` only for offline retrieval measurement. It does not select a production threshold or clinical response policy.
## Required inputs
- Benchmark schema: `kineia.retrieval-benchmark.v1`.
- Corpus inventory schema: `kineia.corpus-inventory.v1`.
- Every relevance label must reference an inventory `(source_id, source_version_id, chunk_index)`.
- `draft` cases are dry-run only. Only `expert_validated` cases enter clinical aggregates, and a mixed report is non-publishable.
Kinesiologists own relevance grades, expected actions, reviewer identity, and consensus. AI may draft cases but MUST NOT mark them `expert_validated`.
## Run
```powershell
python scripts/evaluate_retrieval.py --benchmark benchmark.json --inventory corpus.json --output report.json
```
The harness calls `Retriever.search(limit=20)` and `rerank(top_k=20)`. It reports Hit, Recall, MRR, graded nDCG, and retrieval coverage for both stages. nDCG uses raw grades 0–3 as gains; unknown and repeated hits retain rank but contribute zero gain after the first identity. `runtime_identity` records the configured serving contract, while observed modes/scores describe returned candidates only; zero-result runs keep those sets empty and use `provenance_status=no_results`. Git SHA, dirty state, and source digest bind the report to executed code. JSON `null` means N/A because the denominator or exact adjudication is absent.
## Safety boundaries
Inputs reject unknown fields, duplicate keys/identities, obvious PHI schema fields, and bounded-size violations. Free-text PHI detection is intentionally NOT attempted because it is unreliable; use only synthetic or properly deidentified queries. Reports contain case IDs and digests, never raw queries, fragments, filter values, history, or user IDs. CLI failures emit only sanitized JSON codes.
