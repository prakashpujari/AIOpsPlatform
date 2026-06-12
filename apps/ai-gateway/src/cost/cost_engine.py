"""Cost engine — token counting, per-request cost calculation, daily budget enforcement."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from ..core.config import settings
from ..core.exceptions import BudgetExceededError
from ..registry.schemas import ModelDefinition

logger = logging.getLogger(__name__)

try:
    import tiktoken
    _tiktoken_available = True
    _encoder = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer (close enough for estimation)
except Exception:  # noqa: BLE001
    _tiktoken_available = False
    _encoder = None
    logger.warning("tiktoken unavailable — using character-based token estimation")


def estimate_tokens(text: str) -> int:
    if _tiktoken_available and _encoder:
        return len(_encoder.encode(text))
    # Rough approximation: 4 chars ≈ 1 token
    return max(1, len(text) // 4)


@dataclass
class CostRecord:
    model_id: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str = ""


from prometheus_client import Counter, Gauge

# Metrics for cost monitoring
COST_ALERTS = Counter(
    "gateway_cost_alerts_total",
    "Number of high‑cost alerts triggered"
)
DAILY_SPEND = Gauge(
    "gateway_daily_spend_usd",
    "Current day's total spend in USD"
)

class CostEngine:
    """Tracks spend per day and enforces budget limits."""

    def __init__(self) -> None:
        self._daily_spend: dict[str, float] = {}  # date_str → cumulative USD
        self._records: list[CostRecord] = []

    # ── Public API ───────────────────────────────────────────────────────────

    def estimate_prompt_cost(self, messages: list[dict], model: ModelDefinition) -> float:
        tokens = sum(estimate_tokens(m.get("content", "")) for m in messages)
        return (tokens / 1000) * model.cost_per_1k_prompt_tokens

    def check_budget(self, estimated_cost: float) -> None:
        today = self._today_key()
        spent = self._daily_spend.get(today, 0.0)
        if spent + estimated_cost > settings.daily_budget_usd:
            raise BudgetExceededError(
                f"Daily budget of ${settings.daily_budget_usd:.2f} would be exceeded "
                f"(spent=${spent:.4f}, estimated=${estimated_cost:.4f})"
            )

    def record(
        self,
        model: ModelDefinition,
        prompt_tokens: int,
        completion_tokens: int,
        request_id: str = "",
    ) -> CostRecord:
        cost = (
            (prompt_tokens / 1000) * model.cost_per_1k_prompt_tokens
            + (completion_tokens / 1000) * model.cost_per_1k_completion_tokens
        )
        record = CostRecord(
            model_id=model.id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
            request_id=request_id,
        )
        self._records.append(record)
        today = self._today_key()
        self._daily_spend[today] = self._daily_spend.get(today, 0.0) + cost
        DAILY_SPEND.set(self._daily_spend[today])

        if cost > settings.cost_alert_threshold_usd:
            logger.warning("High-cost request: $%.4f on model %s", cost, model.id)
            # Increment high‑cost alert metric
            COST_ALERTS.inc()

        return record

    def daily_spend(self) -> float:
        return self._daily_spend.get(self._today_key(), 0.0)

    def summary(self) -> dict:
        by_model: dict[str, dict] = {}
        for r in self._records:
            if r.model_id not in by_model:
                by_model[r.model_id] = {"requests": 0, "prompt_tokens": 0,
                                         "completion_tokens": 0, "cost_usd": 0.0}
            by_model[r.model_id]["requests"] += 1
            by_model[r.model_id]["prompt_tokens"] += r.prompt_tokens
            by_model[r.model_id]["completion_tokens"] += r.completion_tokens
            by_model[r.model_id]["cost_usd"] += r.cost_usd
        return {
            "daily_spend_usd": self.daily_spend(),
            "daily_budget_usd": settings.daily_budget_usd,
            "total_requests": len(self._records),
            "by_model": by_model,
        }

    @staticmethod
    def _today_key() -> str:
        return date.today().isoformat()


# Singleton
cost_engine = CostEngine()
