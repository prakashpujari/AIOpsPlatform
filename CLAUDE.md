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
| 2 | Frontend | ✅ Done |
| 3 | Backend | ✅ Done |
| 4 | AI Gateway | ✅ Done |
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

## Upcoming Phases (Brief Outlook)

- **5 – Model Routing**: Implement a router that selects the appropriate LLM based on request metadata (e.g., latency, cost, domain). Includes a policy engine for fallback and throttling.
- **6 – Model Serving**: Deploy LLM inference services (vLLM, TGI) behind the AI Gateway, expose health checks, and add scaling policies.
- **7 – LangGraph Agents**: Build composable agents for workflow orchestration, including error handling, retries, and observability hooks.
- **8 – AIOps**: Introduce automated anomaly detection on telemetry, generate remediation suggestions via agents.
- **9 – Auto Incident Creation**: Integrate with incident management (e.g., PagerDuty) to auto‑create tickets from detected issues.
- **10 – RAG / Ingestion**: Implement document ingestion pipelines, chunking, embedding storage in Milvus, and Retrieval‑Augmented Generation endpoints.
- **11 – Hybrid Search**: Combine vector similarity with keyword filters for robust retrieval.
- **12 – Security**: Harden the platform – static analysis, secret scanning, OPA policies, CI‑CD security checks.
- **13 – Evaluation**: Add benchmark suites for LLM quality, latency, cost, and downstream task performance.
- **14 – Observability**: Expand metrics, tracing, log aggregation, alerting dashboards.
- **15 – Databases**: Add migrations, read‑replica support, and data‑archival strategies.
- **16 – DevSecOps**: Automate security testing in CI, enforce policy compliance, secret detection.
- **17 – Kubernetes**: Containerize services, Helm charts, Helmfile, and GitOps deployment via ArgoCD.
- **18 – High Availability**: Multi‑region failover, load‑balancing, disaster‑recovery drills.
- **19 – Performance**: Profiling, caching strategies, query optimization, CI‑based performance regression testing.
- **20 – Deliverables**: Final documentation, hand‑off checklist, production‑grade release process.

## Contribution Guidelines

1. **Branching** – Create a feature branch from `main` for each phase or issue. Prefix branch names with the phase number, e.g., `phase-5/model-routing`.
2. **Commits** – Follow Conventional Commits (`feat`, `fix`, `chore`, `refactor`, `docs`). Include a brief description and reference any related issue number.
3. **Pull Requests** – PR titles should match the Conventional Commit format. Assign at least one reviewer from the core team and ensure all CI checks pass.
4. **Testing** – Write unit tests for new modules, integration tests for end‑to‑end flows, and add them under `tests/`. Use `pytest` for Python and `jest`/`react-testing-library` for frontend.
5. **Linting** – Run `ruff` (Python) and `npm run lint` (TypeScript) before committing. CI will enforce lint failures as blockers.
6. **Documentation** – Update `docs/` with any architectural decisions, API contracts, or runbooks. Keep docs in Markdown and ensure they build with MkDocs.

## Testing Strategy

- **Unit Tests** – Target 80 % coverage per package. Use `pytest` with fixtures for database mocks.
- **Integration Tests** – Spin up Docker Compose stacks (`docker compose -f infra/docker-compose.yml up`) and run end‑to‑end scenarios.
- **Load Tests** – Use `locust` or `k6` to simulate traffic against the AI Gateway and model serving endpoints.
- **Security Tests** – Run `bandit` and `trivy` in CI; add custom OPA policies for runtime checks.

## Deployment Overview

- **Local Development** – `./scripts/setup/local-dev.sh` sets up PostgreSQL, Redis, Kafka, Milvus, and Keycloak via Docker.
- **Staging / Production** – Deploy using Helm charts stored in `infrastructure/helm/`. CI pipelines (`.github/workflows/*.yml`) build Docker images, push to the container registry, and trigger ArgoCD sync.
- **Feature Flags** – Leverage `launchdarkly`‑style flags in the `config/` package to toggle new functionality without redeploy.

## License

This project is licensed under the **Apache License 2.0**. See `LICENSE` for full terms.

---

## Phase 5 – Model Routing

### Goal
Create a dynamic routing layer that selects the optimal LLM for each request based on intent, cost, latency, health, and any explicit preferences supplied by the caller.

### Core Components
- **`RoutingEngine`** (`apps/ai-gateway/src/router/routing_engine.py`): central singleton that orchestrates candidate selection, strategy application, and fallback chain generation.
- **Strategies** (`apps/ai-gateway/src/router/strategies/`):
  - `intent_strategy.py` – maps user intent to a capability and picks the highest‑priority model that supports it.
  - `cost_strategy.py` – chooses the cheapest model that satisfies optional capability constraints.
  - `latency_strategy.py` – picks the model with the highest tokens‑per‑second throughput.
  - `failover_strategy.py` – builds a graceful degradation chain when the primary model is unavailable.
- **Health Monitoring** (`apps/ai-gateway/src/health/health_monitor.py`) and **Circuit Breakers** (`apps/ai-gateway/src/health/circuit_breaker.py`) provide real‑time status for each model.

### Tasks
1. **Expose Configuration** – add `MODEL_ROUTING_STRATEGY` and `MODEL_ROUTING_PREFERENCE` env vars in `settings.py`.
2. **Complete Fallback Logic** – ensure `get_fallback_chain` respects model health and priority ordering.
3. **Unit Tests** – cover each strategy in isolation and the end‑to‑end routing flow.
4. **Integration Tests** – spin up a minimal set of mock providers (vLLM, Ollama) and verify routing decisions via the `/chat` endpoint.
5. **Documentation** – update `docs/routing.md` with strategy definitions, configuration knobs, and example API calls.

### Design Notes
- The routing decision is represented by the `RoutingDecision` Pydantic model, which is returned to the API layer for logging and observability.
- Fallbacks are automatically recorded in the response metadata payload (see `chat_stream` implementation).
- Future extensions can plug in custom strategies by implementing the `select_*` signature and adding an entry to `_STRATEGY_MAP` in `chat.py`.

---

## Phase 6 – Model Serving

### Goal
Run the selected LLMs behind the AI Gateway, providing a uniform `chat` interface regardless of the underlying provider (vLLM, TGI, Ollama, OpenAI‑compatible, etc.).

### Steps
1. **Provider Abstractions** – `apps/ai-gateway/src/providers/` already contains `vllm_provider.py` and `ollama_provider.py`. Add a thin wrapper for TGI (`tgi_provider.py`) following the same async `chat_stream` / `chat_complete` signatures.
2. **Docker Images** – build lightweight container images for each provider using the official vLLM/TGI/Ollama Dockerfiles. Store them in the `infrastructure/helm/` chart values.
3. **Health Checks** – each provider must expose `/healthz`. Extend `health_monitor.py` to poll these endpoints and update the `ModelHealthState`.
4. **Autoscaling** – configure Kubernetes Horizontal Pod Autoscaler (HPA) based on GPU utilisation and request latency metrics.
5. **Testing** – add integration tests that start provider containers via `docker compose` and verify end‑to‑end request flow through the gateway.

### Observability
- Export per‑model latency, error rate, and token throughput to Prometheus via the existing `health_monitor` metrics.
- Add Grafana dashboards for model utilisation and cost per request.

---

## Phase 7 – LangGraph Agents

### Goal
Introduce composable, stateful agents that can coordinate multi‑step workflows (e.g., incident triage, policy enforcement, data enrichment).

### Work Items
1. **Agent Skeleton** – create a base `BaseAgent` class in `agents/` that handles input validation, tool registration, and structured output.
2. **Example Agents** – implement a `RiskAssessmentAgent` and a `TicketCreationAgent` that demonstrate calling the AI Gateway, persisting intermediate state, and emitting events.
3. **Orchestration Engine** – add a simple async dispatcher that runs agents in parallel, respects rate limits, and aggregates results.
4. **Testing** – unit‑test each agent with mocked LLM responses; add end‑to‑end tests that spin up the full stack.
5. **Documentation** – `docs/agents.md` describing lifecycle, error handling, and best practices.

---

## Phase 8 – AIOps

### Goal
Automatically detect anomalies in telemetry (metrics, logs, traces) and generate actionable remediation suggestions via agents.

### Tasks
- Integrate with Prometheus rule alerts and Loki log alerts.
- Store alert events in a dedicated Postgres table.
- Trigger the `RootCauseAgent` to analyse the event and produce a concise recommendation.
- Provide a UI view in the front‑end dashboard for operators to review suggested actions.

---

## Phase 9 – Auto Incident Creation

### Goal
Create tickets in PagerDuty (or an equivalent incident platform) automatically when high‑severity alerts are raised.

### Tasks
- Add a `PagerDutyClient` wrapper in `apps/ai-gateway/src/providers/`.
- Extend the fallback engine to call the client after an agent produces a `TicketPayload`.
- Ensure idempotency – deduplicate incidents based on a fingerprint.
- Write integration tests using the PagerDuty sandbox API.

---

## Phase 10 – RAG / Ingestion

### Goal
Build a pipeline that ingests documents, chunks them, creates embeddings via the selected LLM, and stores them in Milvus for retrieval.

### Tasks
- Define an `IngestionJob` Celery task (or FastAPI background task) that processes files from a configurable source bucket.
- Implement chunking logic (`Chunker` utility) with overlap to preserve context.
- Use `apps/ai-gateway/src/providers/vllm_provider.py` to obtain embeddings.
- Populate Milvus collections and expose a `/search` endpoint.
- Write end‑to‑end tests that ingest a sample PDF and retrieve relevant passages.

---

## Phase 11 – Hybrid Search

### Goal
Combine dense vector similarity with keyword filtering to improve relevance and control.

### Tasks
- Extend the `/search` endpoint to accept optional `filters` (e.g., document type, date range).
- Implement a two‑stage retrieval: first filter IDs via metadata, then rank with vector similarity.
- Benchmark against pure vector and pure keyword approaches.

---

## Phase 12 – Security

### Goal
Harden the entire stack against common threats and enforce compliance policies.

### Tasks
- Run `bandit` and `trivy` in CI for static analysis of Python and container images.
- Add OPA policies that gate deployments and API calls.
- Enable secret scanning in pull requests (detect hard‑coded credentials).
- Perform a penetration test of the gateway endpoints.

---

## Phase 13 – Evaluation

### Goal
Establish quantitative metrics for LLM performance, cost, and downstream business impact.

### Tasks
- Create a benchmark harness that runs a suite of representative queries across all models.
- Record latency, token usage, and cost via the existing `cost_engine`.
- Add business‑logic metrics (e.g., answer correctness via a ground‑truth dataset).
- Store results in a PostgreSQL table and visualise in Grafana.

---

## Phase 14 – Observability

### Goal
Provide deep visibility into request flow, model health, and cost.

### Tasks
- Export request‑level traces using OpenTelemetry (already integrated in `infra/otel/`).
- Add Prometheus alerts for error spikes, latency regressions, and budget overruns.
- Build Grafana dashboards showing per‑model utilisation, cost per hour, and fallback occurrences.

---

## Phase 15 – Databases

### Goal
Add robustness and scalability to the data layer.

### Tasks
- Implement read‑replica routing for analytics queries.
- Add migration scripts using Alembic and store them in `infrastructure/db/migrations/`.
- Introduce a data‑archival policy that moves old telemetry to cold storage (e.g., S3) after 90 days.

---

## Phase 16 – DevSecOps

### Goal
Integrate security checks directly into the CI/CD pipeline.

### Tasks
- Enforce OPA policies in GitHub Actions (`.github/workflows/ci.yml`).
- Fail builds on high‑severity Bandit findings.
- Add a pre‑commit hook that runs `ruff` and secret scanning.

---

## Phase 17 – Kubernetes

### Goal
Containerise every service and manage deployments via Helm/ArgoCD.

### Tasks
- Write Helm charts for `api`, `ai-gateway`, `web`, and each LLM provider.
- Configure ArgoCD applications with automated sync and health checks.
- Add a `kustomize` layer for environment‑specific overrides (dev, staging, prod).

---

## Phase 18 – High Availability

### Goal
Ensure the platform can survive zone or region failures.

### Tasks
- Deploy multi‑region clusters and configure global load balancing (e.g., Cloudflare Spectrum or GCP Load Balancer).
- Implement data replication for PostgreSQL using logical replication.
- Test failover drills and verify that the routing engine respects region‑aware health signals.

---

## Phase 19 – Performance

### Goal
Continuously optimise latency, throughput, and cost.

### Tasks
- Profile hotspot functions in the routing engine and provider wrappers.
- Add a caching layer (Redis) for prompt embeddings and repetitive queries.
- Introduce a token‑budget enforcement policy that throttles abusive callers.
- Run CI‑based performance regression tests on every PR.

---

## Phase 20 – Deliverables

### Goal
Prepare the final production‑grade release package.

### Tasks
- Consolidate all architecture diagrams and runbooks into `docs/`.
- Perform a final security audit and obtain sign‑off.
- Create a release checklist covering migration steps, rollback plan, and stakeholder communication.
- Tag the repository with `v1.0.0` and publish Helm charts to the public chart repository.

---

*End of CLAUDE.md*