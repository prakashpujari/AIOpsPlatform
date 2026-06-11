"""Cost tracking domain models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CostRecord(BaseModel):
    date: datetime
    model: str
    agent: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float

    model_config = {"from_attributes": True}


class ModelCost(BaseModel):
    model: str
    cost_usd: float


class AgentCost(BaseModel):
    agent: str
    cost_usd: float


class TrendPoint(BaseModel):
    date: str
    cost_usd: float


class CostSummary(BaseModel):
    total_cost_usd: float
    daily_avg_usd: float
    top_models: list[ModelCost]
    top_agents: list[AgentCost]
    trend: list[TrendPoint]
