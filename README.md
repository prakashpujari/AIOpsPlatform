# Enterprise Banking AI Support Copilot — AIOps Platform

Production-grade, banking-compliant, cloud-agnostic AI platform for:
- Production Support & Incident Management
- AIOps & Root Cause Analysis
- Knowledge Retrieval (RAG)
- Auto Incident Creation (ServiceNow / Jira)
- Auto Remediation Recommendations
- Mortgage & Banking Operations Support

## Architecture

```
apps/          → Frontend (Next.js), Backend (FastAPI), AI Gateway, Ingestion
agents/        → LangGraph agents (Intent, Search, RCA, Remediation, Incident, Evaluation, Compliance, Escalation)
infrastructure/ → Terraform, Kubernetes, Helm, ArgoCD
observability/ → Prometheus, Grafana, Loki, Jaeger, OpenTelemetry
docs/          → Architecture, API, Runbooks, Security, DR
tests/         → Unit, Integration, E2E, Load, Security
scripts/       → Setup, Deploy, Migrate, Backup
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Next.js 15, TypeScript, TailwindCSS, Material UI |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 |
| AI Gateway | Custom FastAPI service with model routing |
| LLM Models | Llama 3.3 70B, DeepSeek R1/Coder, Qwen 3, Phi-4, Gemma |
| Model Serving | vLLM, KServe, Ray Serve |
| Agents | LangGraph, LangChain |
| Vector DB | Milvus |
| Embeddings | BGE-M3 |
| Reranking | BGE-Reranker-v2 |
| Document Parsing | IBM Docling, PyMuPDF, Unstructured |
| Databases | PostgreSQL 16, Redis 7, Apache Kafka 3.6 |
| Object Store | MinIO |
| Auth | Keycloak, OAuth2, OIDC, JWT |
| Security | HashiCorp Vault, OPA, Falco |
| Observability | Prometheus, Grafana, Loki, Jaeger, OpenTelemetry |
| CI/CD | GitHub Actions, Jenkins, ArgoCD |
| Infrastructure | Terraform, Kubernetes, Helm |
| Evaluation | DeepEval, RAGAS |

## Quick Start

```bash
./scripts/setup/local-dev.sh
```

## Local Development

For a step‑by‑step guide on running the full stack locally (including required environment variables, manual alternatives, verification commands, and UI screenshot instructions), see the documentation at **[docs/local-dev.md](docs/local-dev.md)**.

## Phases

- Phase 1: Project Structure ✅
- Phase 2: Frontend (Next.js)
- Phase 3: Backend (FastAPI)
- Phase 4: AI Gateway
- Phase 5: Model Routing
- Phase 6: Model Serving
- Phase 7: LangGraph Agents
- Phase 8: AIOps
- Phase 9: Auto Incident Creation
- Phase 10: RAG / Document Ingestion
- Phase 11: Hybrid Search
- Phase 12: Security
- Phase 13: Evaluation
- Phase 14: Observability
- Phase 15: Databases
- Phase 16: DevSecOps
- Phase 17: Kubernetes
- Phase 18: High Availability
- Phase 19: Performance
- Phase 20: Deliverables

## Compliance

Designed for Fortune 100 financial institutions — SOC 2, PCI-DSS, GDPR, FFIEC.
