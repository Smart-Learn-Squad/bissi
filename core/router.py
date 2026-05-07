"""Model router for BISSI v2 (single-model local deployment)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Set

from core.config import DEFAULT_CONFIG

Model = Literal["gemma4:e2b"]


@dataclass
class RouteResult:
    """Model route decision payload."""

    model: Model
    score: float
    reason: str
    domains: Set[str] = field(default_factory=set)


class ModelRouter:
    """Keep router contract stable while forcing the production model."""

    def score(self, prompt: str) -> tuple[float, list[str], Set[str]]:
        """Return a lightweight score tuple for compatibility."""
        prompt_len = len(prompt or "")
        score = min(1.0, round(prompt_len / 500.0, 3))
        return score, [f"single_model_mode length={prompt_len}"], set()

    def route(self, prompt: str, threshold_adjustment: float = 0.0) -> RouteResult:
        """Return the fixed local model route decision."""
        score, reasons, domains = self.score(prompt)
        return RouteResult(
            model=DEFAULT_CONFIG.llama_cpp.model,
            score=score,
            reason=" | ".join(reasons),
            domains=domains,
        )


_router = ModelRouter()


def route(prompt: str, threshold_adjustment: float = 0.0) -> RouteResult:
    """Public routing entrypoint."""
    return _router.route(prompt, threshold_adjustment)
