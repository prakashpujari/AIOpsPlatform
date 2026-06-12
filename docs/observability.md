# Observability

This document describes the observability stack for the **AI Gateway** service (Phase 14). All services expose Prometheus metrics and OpenTelemetry traces. The metrics are collected by Prometheus, stored, and visualised in Grafana dashboards. Alerts are defined in PrometheusRule yaml files.

## Prometheus metrics

| Metric | Type | Description |
|--------|------|-------------|
| `gateway_requests_total` | Counter | Total number of requests received by the gateway (labels: `method`, `endpoint`, `status`). |
| `gateway_request_duration_seconds` | Histogram | Latency of each request (label: `endpoint`). |
| `gateway_model_requests_total` | Counter | Number of routing decisions that selected each model (label: `model`). |
| `gateway_model_latency_seconds` | Histogram | Latency of routing handling per model (label: `model`). |
| `gateway_routing_decisions_total` | Counter | Count of routing decisions by strategy and model (labels: `strategy`, `model`). |
| `gateway_model_health` | Gauge | Health status of each model (0=unknown, 1=healthy, 2=degraded, 3=unhealthy, 4=circuit_open). |
| `gateway_model_latency_ms` | Gauge | Most‑recent latency observed for each model (label: `model`). |
| `gateway_circuit_state` | Gauge | Circuit‑breaker state per model (0=closed, 1=open, 2=half‑open). |
| `gateway_cost_alerts_total` | Counter | Number of high‑cost alerts triggered (cost > `settings.cost_alert_threshold_usd`). |
| `gateway_daily_spend_usd` | Gauge | Current day's total spend in USD. |
| `gateway_cost_alerts_total` | Counter | Number of high‑cost alerts triggered. |
| `gateway_model_requests_total` | Counter | Requests routed to each model. |

All metrics are exposed via the `/metrics` endpoint (FastAPI route defined in `apps/ai-gateway/src/main.py`).

## OpenTelemetry tracing

The gateway is instrumented with OpenTelemetry using the `setup_tracing` helper from `apps/api/src/core/tracing.py`. Traces are exported to an OTLP collector configured via environment variables (`OTEL_EXPORTER_OTLP_ENDPOINT`). The following spans are automatically created:
- HTTP request handling (FastAPI middleware).
- Model health checks (internal async tasks).
- Routing decisions.
- Cost engine calculations.

## Grafana dashboards

Dashboard JSON files are stored under `observability/grafana/`. Import them into Grafana to visualise:
- **Gateway Overview** – request rates, error rates, latency distribution.
- **Model Health** – health status gauge, latency, circuit‑breaker state.
- **Cost Monitoring** – daily spend, high‑cost alert count.

## Prometheus alert rules

Alert rules are defined in `observability/prometheus/alerts.yml`. They fire when:
- Model health becomes `unhealthy` or `circuit_open` for more than 5 minutes.
- Request latency exceeds 2 seconds for a given endpoint (5‑minute sliding window).
- Daily spend exceeds 90 % of the configured daily budget.
- High‑cost alert counter increases rapidly (more than 5 alerts in 10 minutes).

## Deployment notes

- Ensure the Prometheus server scrapes `/metrics` from the AI Gateway service.
- Deploy the OTLP collector (e.g., the OpenTelemetry Collector) and configure `settings.otel_exporter_otlp_endpoint`.
- Add the Grafana dashboards and alert rules to the respective monitoring repositories.
