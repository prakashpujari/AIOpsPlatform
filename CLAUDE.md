# CLAUDE.md — Enterprise AI Platform

## Project Overview

Enterprise Banking AI Support Copilot & AIOps Platform.
Built phase-by-phase; each phase is committed before the next begins.

## Repository Layout

```
apps/          → Deployable services (web, api, ai-gateway, ingestion)
agents/        → LangGraph agent implementations
infrastructure/ → IaC (Terraform, Helm, ArgoCD, K8s manifests)
observability/ → Prometheus, Grafana, Loki, Jaeger, OTel configs
docs/          → Architecture docs, runbooks, security docs
tests/         → Unit, integration, E2E, load, security tests
scripts/       → Dev setup, migrations, backups
.github/       → CI/CD workflows
```

## Tech Stack

- **Frontend**: Next.js 15, React 19, TypeScript, TailwindCSS, MUI
- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2
- **AI Gateway**: FastAPI + custom routing/policy engine
- **Agents**: LangGraph, LangChain
- **LLMs**: Llama 3.3 70B, DeepSeek R1/Coder, Qwen 3, Phi-4, Gemma (via vLLM)
- **Vector DB**: Milvus 2.4
- **DBs**: PostgreSQL 16, Redis 7, Kafka 3.6
- **Auth**: Keycloak 24, OAuth2/OIDC, JWT
- **Security**: HashiCorp Vault, OPA, Bandit, Trivy
- **Observability**: Prometheus, Grafana, Loki, Jaeger, OpenTelemetry
- **IaC**: Terraform, Helm, ArgoCD, GitHub Actions

## Development Commands

```bash
# Start full local stack
./scripts/setup/local-dev.sh

# Backend API
cd apps/api && poetry run uvicorn src.main:app --reload

# AI Gateway
cd apps/ai-gateway && poetry run uvicorn src.main:app --port 8001 --reload

# Frontend
cd apps/web && npm run dev

# Run tests
cd apps/api && poetry run pytest tests/ -v

# Lint Python
ruff check apps/ agents/

# Lint TypeScript
cd apps/web && npm run lint
```

## Code Conventions

- Python: PEP 8, type annotations required, ruff + mypy
- TypeScript: strict mode, no `any`
- No inline secrets — all secrets via Vault or env vars
- All HTTP handlers must have Pydantic request/response models
- All DB access through repository pattern
- Agents never call LLMs directly — always via AI Gateway

## Phase Tracker

| Phase | Title | Status |
|-------|-------|--------|
| 1 | Project Structure | ✅ Done |
| 2 | Frontend | ⏳ Next |
| 3 | Backend | ⬜ |
| 4 | AI Gateway | ⬜ |
| 5 | Model Routing | ⬜ |
| 6 | Model Serving | ⬜ |
| 7 | LangGraph Agents | ⬜ |
| 8 | AIOps | ⬜ |
| 9 | Auto Incident Creation | ⬜ |
| 10 | RAG / Ingestion | ⬜ |
| 11 | Hybrid Search | ⬜ |
| 12 | Security | ⬜ |
| 13 | Evaluation | ⬜ |
| 14 | Observability | ⬜ |
| 15 | Databases | ⬜ |
| 16 | DevSecOps | ⬜ |
| 17 | Kubernetes | ⬜ |
| 18 | High Availability | ⬜ |
| 19 | Performance | ⬜ |
| 20 | Deliverables | ⬜ |
