#!/bin/bash
set -euo pipefail

# KineIA SSL Setup Script
# Obtains a Let's Encrypt certificate for the domain and configures auto-renewal.
# Usage: DOMAIN=example.com LETSENCRYPT_EMAIL=admin@example.com ./scripts/setup-ssl.sh

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# --- Load environment ---
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# --- Validate required variables ---
: "${DOMAIN:?ERROR: DOMAIN is not set. Export DOMAIN=your-domain.com}"
: "${LETSENCRYPT_EMAIL:?ERROR: LETSENCRYPT_EMAIL is not set. Export LETSENCRYPT_EMAIL=your-email@example.com}"

echo "=== KineIA SSL Setup ==="
echo "Domain:      $DOMAIN"
echo "Email:       $LETSENCRYPT_EMAIL"
echo ""

# --- Check / install certbot ---
install_certbot() {
    if command -v certbot &> /dev/null; then
        echo "[✓] certbot is already installed"
        return 0
    fi

    echo "[…] certbot not found — installing…"

    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq certbot
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y certbot
    elif command -v yum &> /dev/null; then
        sudo yum install -y certbot
    elif command -v apk &> /dev/null; then
        sudo apk add --no-cache certbot
    else
        echo "ERROR: Unsupported package manager. Install certbot manually: https://certbot.eff.org/"
        exit 1
    fi

    echo "[✓] certbot installed"
}

# --- Obtain certificate ---
obtain_cert() {
    echo "[…] Requesting Let's Encrypt certificate for $DOMAIN…"

    # Ensure nginx is running so ACME challenge can be served
    if ! docker compose -f "$PROJECT_DIR/docker-compose.yml" ps nginx | grep -q "Up"; then
        echo "[…] Starting nginx for ACME challenge…"
        docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d nginx
        sleep 3
    fi

    # Use standalone or webroot mode — webroot is preferred with running nginx
    sudo certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --non-interactive \
        --agree-tos \
        --email "$LETSENCRYPT_EMAIL" \
        -d "$DOMAIN" \
        --keep-until-expiring \
        --expand 2>&1 | tee /tmp/certbot_output.log

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "[✓] Certificate obtained for $DOMAIN"
    else
        echo "ERROR: certbot failed. Check /tmp/certbot_output.log"
        exit 1
    fi
}

# --- Setup auto-renewal ---
setup_auto_renewal() {
    local cron_line="0 3 * * * certbot renew --quiet --post-hook 'docker compose -f \"$PROJECT_DIR/docker-compose.yml\" exec nginx nginx -s reload'"

    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -qF "certbot renew"; then
        echo "[✓] Certbot renewal cron job already exists"
        return 0
    fi

    echo "[…] Adding certbot auto-renewal cron job (daily at 3 AM)…"
    (crontab -l 2>/dev/null || true; echo "$cron_line") | crontab -
    echo "[✓] Cron job added"
}

# --- Main ---
install_certbot
obtain_cert
setup_auto_renewal

echo ""
echo "=== SSL Setup Complete ==="
echo "  Certificate path: /etc/letsencrypt/live/$DOMAIN/"
echo "  Auto-renewal:     daily at 3 AM via cron"
echo "  Test renewal:     sudo certbot renew --dry-run"
