# Local Development Without Docker

This guide explains how to run the Enterprise AI Platform locally **without Docker**, using a mock API server for backend services. This is useful for UI development, frontend testing, and capturing screenshots for documentation.

> **Note**: For full-stack development with real databases and services, use the standard Docker-based setup:
> ```bash
> ./scripts/setup/local-dev.sh
> ```

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 20+ | Frontend development |
| npm | 10+ | Package management |
| Python | 3.11+ | Backend development (optional) |
| Git | Latest | Version control |

## Quick Start (Frontend + Mock API)

### 1. Install Frontend Dependencies

```bash
cd apps/web
npm install
```

### 2. Create Local Environment File

Create `apps/web/.env.local`:

```env
# Mock API for local development without Docker
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AI_GATEWAY_URL=http://localhost:8000
NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8080
NEXT_PUBLIC_KEYCLOAK_REALM=aiops-platform
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=web-client
NEXTAUTH_SECRET=super-secret-key-that-is-32+bytes-long
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_TRUST_HOST=true
```

### 3. Start Mock API Server

From the project root:

```bash
# Install mock server dependencies (one-time)
npm install express cors

# Start mock API server on port 8000
node mock-api-server.js
```

The mock API provides:
- **Health check**: `http://localhost:8000/health`
- **Incidents CRUD**: `/api/v1/incidents`
- **Metrics**: `/api/v1/metrics/summary`, `/api/v1/metrics/timeseries`
- **Chat/AI Gateway**: `/v1/chat` (streaming & non-streaming)
- **Dashboard stats**: `/api/v1/dashboard/stats`
- **Root Cause Analysis**: `/api/v1/rca/:incidentId`
- **Runbooks**: `/api/v1/runbooks`
- **Auth**: `/api/v1/auth/login`, `/api/v1/auth/me`

### 4. Start Frontend Development Server

```bash
cd apps/web
npm run dev
```

Frontend will be available at: **http://localhost:3000**

### 5. Login

Use the "Development Credentials Login" section on the login page:

- **Email**: `admin@bank.internal`
- **Password**: `password123`

Or any email/password combination (mock auth accepts any credentials).

## UI Screenshots

The following screenshots show the main UI pages captured during local development:

### Login Page
![Login Page](screenshots/01-login-page.png)

### Credentials Login Form
![Credentials Login](screenshots/02-login-credentials-open.png)

### Dashboard Overview
![Dashboard Overview](screenshots/03-dashboard-overview.png)

### Incidents List
![Incidents List](screenshots/04-incidents-list.png)

### AI Chat / Copilot
![Chat Page](screenshots/06-chat-page.png)

### Metrics & Monitoring
![Metrics Page](screenshots/09-metrics-page.png)

### Settings
![Settings Page](screenshots/10-settings-page.png)

### Runbooks
![Runbooks Page](screenshots/11-runbooks-page.png)

### Root Cause Analysis
![RCA Page](screenshots/12-rca-page.png)

### Mobile View (Dashboard)
![Mobile Dashboard](screenshots/13-dashboard-mobile.png)

## Running Full Backend Locally (Advanced)

If you need the real Python backend (FastAPI) with SQLite database:

### 1. Set Up Python Environment

```bash
cd apps/api
python3.11 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -U pip setuptools wheel
```

### 2. Install Dependencies (without asyncpg)

```bash
pip install fastapi uvicorn pydantic pydantic-settings sqlalchemy aiosqlite alembic redis httpx python-jose python-multipart structlog opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-sqlalchemy opentelemetry-instrumentation-redis prometheus-client tenacity hvac tiktoken presidio-analyzer presidio-anonymizer cachetools aiokafka opentelemetry-instrumentation-asyncpg
```

### 3. Configure SQLite Database

Modify `apps/api/src/core/config.py` to accept SQLite URLs:

```python
# Change database_url type from PostgresDsn to str
database_url: str = Field(
    default="postgresql+asyncpg://aiops:changeme@localhost:5432/aiops_platform"
)
```

### 4. Fix SQLAlchemy Reserved Name

In `apps/api/src/infrastructure/database/models.py`, rename `metadata` field:

```python
# Line ~193: metadata -> doc_metadata
doc_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
```

### 5. Run with SQLite

```bash
DATABASE_URL="sqlite+aiosqlite:///./test.db" REDIS_URL="redis://localhost:6379/0" \
  python -m uvicorn src.main:app --reload --port 8000
```

> **Note**: This requires Redis running locally. Install Redis on Windows via [Memurai](https://www.memurai.com/) or use WSL2.

## Architecture Overview (Local Dev)

```
┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│  Mock API       │
│  (Next.js 15)   │     │  (Express.js)   │
│  Port 3000      │     │  Port 8000      │
└─────────────────┘     └─────────────────┘
         │                       │
         │              ┌────────┴────────┐
         │              │  Mock Data      │
         └──────────────│  - Incidents    │
                        │  - Metrics      │
                        │  - Chat/RCA     │
                        │  - Runbooks     │
                        └─────────────────┘
```

## Capturing New Screenshots

To capture updated screenshots:

```bash
cd apps/web
npm install -D @playwright/test playwright
npx playwright install chromium
node screenshot-test.js
```

Screenshots will be saved to `apps/web/screenshots/` and can be copied to `docs/screenshots/`.

## Troubleshooting

### Port Already in Use

```bash
# Find process on port 3000
netstat -ano | findstr :3000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

### Frontend Build Errors

```bash
cd apps/web
rm -rf .next node_modules
npm install
npm run dev
```

### Mock API Not Responding

Ensure the mock server is running:
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok","service":"mock-api","version":"1.0.0"}
```

### Authentication Issues

The development credentials provider accepts any email/password. If login fails:
1. Clear browser cookies for `localhost:3000`
2. Check browser console for errors
3. Verify `NEXTAUTH_SECRET` is set in `.env.local`

## Next Steps

- For full backend development: Use Docker Compose (`./scripts/setup/local-dev.sh`)
- For model serving: Deploy vLLM/Ollama via Docker or Kubernetes
- For production: Use Helm charts in `infrastructure/helm/`

---

*Last updated: 2026-06-12*
*Screenshots captured with Playwright on Next.js 15.1.0*