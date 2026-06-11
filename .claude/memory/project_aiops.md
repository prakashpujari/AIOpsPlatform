---
name: project-aiops-platform
description: Enterprise Banking AI Support Copilot & AIOps Platform — 20-phase build in progress
metadata:
  type: project
---

Building a 20-phase enterprise banking AI platform at C:\pp\GitHub\AIOpsPlatform (branch: main).

**Phase 1 DONE** (commit 668c441) — full monorepo scaffold.

**Why:** Fortune 100 banking-grade production system covering AIOps, RAG, LangGraph agents, auto incident creation, hybrid search, evaluation, and full observability.

**How to apply:** Each phase is implemented fully, tested, then committed before the next begins. Always check CLAUDE.md for current phase status and conventions.

Key decisions made:
- Agents NEVER call LLMs directly — always route through AI Gateway
- Clean Architecture + CQRS + DDD + Repository pattern for backend
- All secrets via HashiCorp Vault or env vars (never hardcoded)
- Multi-stage Dockerfiles for every service (development + production targets)
