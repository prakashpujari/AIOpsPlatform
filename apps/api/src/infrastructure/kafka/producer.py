"""Kafka event producer with retry and structured events."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import structlog
from aiokafka import AIOKafkaProducer
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ...core.config import settings

logger = structlog.get_logger(__name__)

_producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            enable_idempotence=True,
            compression_type="gzip",
            max_batch_size=16384,
            linger_ms=10,
        )
        await _producer.start()
    return _producer


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=0.5, max=5),
    retry=retry_if_exception_type(Exception),
)
async def publish_event(
    topic: str,
    event_type: str,
    payload: dict[str, Any],
    key: str | None = None,
) -> None:
    producer = await get_producer()
    envelope = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    await producer.send_and_wait(topic, value=envelope, key=key)
    logger.info("kafka.event_published", topic=topic, event_type=event_type)


async def publish_incident_event(event_type: str, incident_id: str, payload: dict[str, Any]) -> None:
    await publish_event(settings.kafka_topic_incidents, event_type, payload, key=incident_id)


async def publish_audit_event(payload: dict[str, Any]) -> None:
    await publish_event(settings.kafka_topic_audit, "audit.action", payload)


async def close_producer() -> None:
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
