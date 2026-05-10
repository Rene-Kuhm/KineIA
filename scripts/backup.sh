#!/bin/bash
set -euo pipefail

# KineIA Backup Script
# Backs up PostgreSQL (pg_dump) and Qdrant (snapshot) with timestamped files.
# Keeps the last BACKUP_RETENTION_DAYS of backups (default: 7), deletes older ones.
# Usage: ./scripts/backup.sh

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# --- Load environment ---
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# --- Configuration ---
readonly BACKUP_DIR="$PROJECT_DIR/backups"
readonly RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
readonly TIMESTAMP=$(date -u +"%Y-%m-%dT%H%M%SZ")
readonly DB_USER="${DB_USER:-kineia}"
readonly DB_NAME="${DB_NAME:-kineia}"
readonly DB_PASSWORD="${DB_PASSWORD:?ERROR: DB_PASSWORD must be set in .env}"

echo "=== KineIA Backup ==="
echo "Timestamp:       $TIMESTAMP"
echo "Backup dir:      $BACKUP_DIR"
echo "Retention days:  $RETENTION_DAYS"
echo ""

# --- Ensure backup directory exists ---
mkdir -p "$BACKUP_DIR"

# --- Backup PostgreSQL ---
echo "[1/3] Backing up PostgreSQL..."
readonly PG_BACKUP_FILE="$BACKUP_DIR/postgres_${TIMESTAMP}.dump"

docker compose -f docker-compose.yml exec -T postgres \
    pg_dump \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-owner \
        --no-acl \
        --format=custom \
        > "$PG_BACKUP_FILE" 2>&1 || {
    echo "ERROR: PostgreSQL backup failed"
    exit 1
}

readonly PG_SIZE=$(du -h "$PG_BACKUP_FILE" | cut -f1)
echo "[✓] PostgreSQL backup: $PG_BACKUP_FILE ($PG_SIZE)"
echo ""

# --- Backup Qdrant ---
echo "[2/3] Backing up Qdrant..."
readonly QDRANT_BACKUP_DIR="$BACKUP_DIR/qdrant_${TIMESTAMP}"
mkdir -p "$QDRANT_BACKUP_DIR"

# Qdrant snapshot API — create snapshot for the collection
readonly QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
readonly COLLECTION="${QDRANT_COLLECTION:-kineia_knowledge}"

# Create snapshot via Qdrant REST API
SNAPSHOT_RESPONSE=$(curl -sf -X POST "$QDRANT_URL/collections/$COLLECTION/snapshots" \
    -H "Content-Type: application/json" \
    -d '{}' 2>&1) || {
    echo "WARNING: Could not create Qdrant snapshot via API. Is Qdrant running?"
    echo "  Response: $SNAPSHOT_RESPONSE"
}

if [ -n "${SNAPSHOT_RESPONSE:-}" ]; then
    echo "[✓] Qdrant snapshot created"
else
    # Fallback: copy Qdrant storage volume data
    echo "[…] Falling back to volume copy for Qdrant..."
    docker compose -f docker-compose.yml cp \
        qdrant:/qdrant/storage "$QDRANT_BACKUP_DIR/storage" 2>&1 || {
        echo "WARNING: Qdrant volume copy also failed. Skipping Qdrant backup."
    }
fi

readonly QDRANT_SIZE=$(du -sh "$QDRANT_BACKUP_DIR" 2>/dev/null | cut -f1 || echo "N/A")
echo "[✓] Qdrant backup: $QDRANT_BACKUP_DIR ($QDRANT_SIZE)"
echo ""

# --- Cleanup old backups ---
echo "[3/3] Cleaning backups older than $RETENTION_DAYS days..."

cleanup_old() {
    local pattern="$1"
    local label="$2"
    local deleted=0

    # Find files older than RETENTION_DAYS and delete them
    find "$BACKUP_DIR" -maxdepth 1 -name "${pattern}*" -type f -mtime +"$RETENTION_DAYS" | while IFS= read -r file; do
        echo "  Deleting: $(basename "$file")"
        rm -f "$file"
        deleted=$((deleted + 1))
    done

    # Also clean directories (for Qdrant folder backups)
    find "$BACKUP_DIR" -maxdepth 1 -name "${pattern}*" -type d -mtime +"$RETENTION_DAYS" | while IFS= read -r dir; do
        echo "  Deleting: $(basename "$dir")"
        rm -rf "$dir"
        deleted=$((deleted + 1))
    done
}

cleanup_old "postgres_" "PostgreSQL"
cleanup_old "qdrant_" "Qdrant"

echo ""
echo "=== Backup Complete ==="
echo "PostgreSQL: $PG_BACKUP_FILE"
echo "Qdrant:     $QDRANT_BACKUP_DIR"
echo ""
echo "Restore PostgreSQL: pg_restore -U kineia -d kineia $PG_BACKUP_FILE"
