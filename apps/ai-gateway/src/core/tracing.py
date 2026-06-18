"""OpenTelemetry tracing setup for the AI Gateway."""

from __future__ import annotations

import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


def setup_tracing(
    service_name: str,
    otlp_endpoint: str,
    enabled: bool = True,
) -> None:
    """Initialize OpenTelemetry tracing if enabled.

    Args:
        service_name: The name of the service for tracing.
        otlp_endpoint: The OTLP exporter endpoint.
        enabled: Whether to enable tracing.
    """
    if not enabled:
        logger.info("Tracing disabled via configuration")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource(attributes={"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        logger.info("OpenTelemetry tracing initialized for %s", service_name)
    except ImportError:
        logger.warning("OpenTelemetry packages unavailable — tracing disabled")
    except Exception:  # noqa: BLE001
        logger.warning("Failed to initialize tracing — running without observability")