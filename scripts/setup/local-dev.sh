#!/usr/bin/env bash
# ─────────────────────────────────────────────
# Local Development Setup Script
# ─────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

log() { echo -e "${GREEN}[SETUP]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

check_deps() {
    log "Checking dependencies..."
    for cmd in docker docker-compose python3 node npm; do
        command -v "$cmd" >/dev/null 2>&1 || error "$cmd is required but not installed."
    done
    python3 --version | grep -q "3.1[2-9]" || error "Python 3.12+ required"
    node --version | grep -qE "v2[0-9]" || warn "Node 20+ recommended"
    log "All dependencies satisfied."
}

setup_env() {
    log "Setting up environment..."
    if [ ! -f "$ROOT_DIR/.env" ]; then
        cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
        warn ".env created from .env.example — update passwords before use"
    else
        log ".env already exists, skipping"
    fi
}

start_infrastructure() {
    log "Starting infrastructure services..."
    cd "$ROOT_DIR"
    docker-compose up -d postgres redis zookeeper kafka milvus-etcd milvus-minio milvus minio vault keycloak
    log "Waiting for services to be healthy..."
    sleep 15
}

run_migrations() {
    log "Running database migrations..."
    cd "$ROOT_DIR/apps/api"
    if command -v poetry >/dev/null 2>&1; then
        poetry run alembic upgrade head
    else
        warn "poetry not found — skipping migrations"
    fi
}

start_observability() {
    log "Starting observability stack..."
    cd "$ROOT_DIR"
    docker-compose up -d prometheus grafana loki jaeger otel-collector
}

start_apps() {
    log "Starting application services..."
    cd "$ROOT_DIR"
    docker-compose up -d api ai-gateway ingestion web
}

main() {
    log "Enterprise AI Platform — Local Dev Setup"
    check_deps
    setup_env
    start_infrastructure
    run_migrations
    start_observability
    start_apps
    echo ""
    log "Setup complete!"
    echo ""
    echo "  Frontend:      http://localhost:3000"
    echo "  API:           http://localhost:8000/docs"
    echo "  AI Gateway:    http://localhost:8001/docs"
    echo "  Keycloak:      http://localhost:8080"
    echo "  Grafana:       http://localhost:3001"
    echo "  Jaeger:        http://localhost:16686"
    echo "  Prometheus:    http://localhost:9090"
    echo "  Milvus:        http://localhost:19530"
    echo "  Vault:         http://localhost:8200"
    echo ""
}

main "$@"
