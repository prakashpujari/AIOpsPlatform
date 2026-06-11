"""Evaluation domain models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class EvalMetrics(BaseModel):
    faithfulness: float = 0.0
    relevancy: float = 0.0
    groundedness: float = 0.0
    hallucination: float = 0.0
    toxicity: float = 0.0
    bias: float = 0.0


class EvalResult(BaseModel):
    id: uuid.UUID
    run_name: str
    agent_type: str
    timestamp: datetime
    metrics: EvalMetrics
    total_samples: int
    pass_rate: float
    ci_gate_status: Literal["pass", "fail", "warn"]

    model_config = {"from_attributes": True}
