# Backfill and verify the hybrid collection
Backfill mutates only v2 via insert-only: it never changes read mode/aliases, legacy data, or deletes; keep legacy reads authoritative until `"ready": true`.
1. **Preflight:** Confirm Qdrant is `1.18.2` or newer and names are distinct; run `uv run --project backend --no-sync python backend/scripts/qdrant_preflight.py`; stop on any error.
2. **Snapshot legacy:** Create a Qdrant snapshot; record its location and prove restore access.
3. **Provision inactive v2:** Run `uv run --project backend --no-sync python backend/scripts/provision_hybrid.py`; require `created`, `updated`, or `compatible`.
4. **Enable dual writes:** Set `QDRANT_WRITE_MODE=dual`, restart ingestion, ingest a controlled document, and confirm its exact ID/payload in both collections.
5. **Backfill bounded pages:** Run `uv run --project backend --no-sync python backend/scripts/hybrid_migration.py backfill --page-size 100`. Atomic `insert_only` protects newer dual writes. Restart from zero or pass `next_offset` via `--offset`; use `--max-pages` for a work window and resolve every error.
6. **Pause and reconcile:** Pause administrative ingestion only, rerun backfill from zero, then run `uv run --project backend --no-sync python backend/scripts/hybrid_migration.py verify --page-size 100`. JSON has bounded samples, exact `discrepancy_counts`, and `truncated` flags. Cutover requires equal counts/digests, 100% dense+sparse coverage, and zero discrepancies; otherwise resume dual mode and investigate without deleting.
7. **Rollback:** Before later cutover, restore `QDRANT_WRITE_MODE=legacy` and restart ingestion. Keep legacy reads and the snapshot authoritative; restoring a snapshot is a separate approved incident action.
