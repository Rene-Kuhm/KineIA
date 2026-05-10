#!/bin/bash
set -euo pipefail

# KineIA Deploy Script
# Pulls latest code, builds images, restarts services, runs migrations, and performs health checks.
# Usage: ./scripts/deploy.sh

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# --- Load environment ---
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

echo "=== KineIA Deploy ==="
echo "Started at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

# --- Step 1: Pull latest changes ---
echo "[1/6] Pulling latest changes from git..."
git pull origin main 2>&1 || {
    echo "WARNING: git pull failed — continuing with local changes"
}
echo ""

# --- Step 2: Build Docker images ---
echo "[2/6] Building Docker images..."
docker compose -f docker-compose.yml build --pull --no-cache 2>&1 || {
    echo "ERROR: Docker build failed"
    exit 1
}
echo "[✓] Images built"
echo ""

# --- Step 3: Restart services ---
echo "[3/6] Restarting services..."
docker compose -f docker-compose.yml down --remove-orphans
docker compose -f docker-compose.yml up -d
echo "[✓] Services started"
echo ""

# --- Step 4: Run database migrations ---
echo "[4/6] Running database migrations..."
docker compose -f docker-compose.yml exec -T backend alembic upgrade head 2>&1 || {
    echo "WARNING: Migration may have failed or already applied. Check alembic logs."
}
echo ""

# --- Step 5: Health checks ---
echo "[5/6] Running health checks..."

# Give services a moment to stabilize
sleep 5

# Check backend
echo -n "  Backend (localhost:8000/health): "
if curl -sf -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null | grep -q "200"; then
    echo "✓ UP"
else
    echo "✗ DOWN — retrying in 5s..."
    sleep 5
    if curl -sf -o /dev/null http://localhost:8000/health 2>/dev/null; then
        echo "  Backend: ✓ UP (after retry)"
    else
        echo "ERROR: Backend health check failed after retry"
    fi
fi

# Check frontend
echo -n "  Frontend (localhost:3000): "
if curl -sf -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null | grep -q "200\|304\|308"; then
    echo "✓ UP"
else
    echo "✗ DOWN — retrying in 5s..."
    sleep 5
    if curl -sf -o /dev/null http://localhost:3000 2>/dev/null; then
        echo "  Frontend: ✓ UP (after retry)"
    else
        echo "WARNING: Frontend health check failed — it may still be starting"
    fi
fi
echo ""

# --- Step 6: Summary ---
echo "[6/6] Deploy Summary"
echo "---"
docker compose -f docker-compose.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "=== Deploy completed at $(date -u +"%Y-%m-%dT%H:%M:%SZ") ==="
