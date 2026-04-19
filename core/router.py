"""ModelRouter — BISSI now uses only gemma4:e2b.

As of 2026-04-17, all requests use gemma4:e2b exclusively.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal, Set

Model = Literal["gemma4:e2b"]

# ── Signal tables ──────────────────────────────────────────────

_HEAVY: Set[str] = {
    # Reasoning & analysis
    "analyse", "analyze",
    "compare", "comparison",
    "explain",
    "summarize", "summarise", "summary", "synthesis", "resume",
    "interpret",
    # Document generation
    "generate", "write", "compose",
    "create", "produce",
    "report", "presentation", "pptx", "docx", "document",
    # Code
    "code", "script", "program", "implement",
    "debug", "optimize", "refactor",
    "function", "class", "algorithm", "python",
    # Data
    "calculate", "statistic", "statistics", "chart", "visualize",
    "pivot", "table", "predict", "model", "regression", "correlation",
    "dataframe", "pandas", "numpy", "average", "mean", "sum",
    "data", "process", "transform",
    # Multi-file / batch
    "batch", "convert",
}

_LIGHT: Set[str] = {
    # Navigation & listing
    "list", "show", "display", "open", "which", "what",
    "where", "find", "search",
    # Simple operations
    "copy", "paste", "rename", "move", "delete", "clipboard",
    # Short factual questions
    "version", "how many", "date", "time",
}

_MULTISTEP: Set[str] = {
    "then", "next", "after", "also", "finally",
    "first", "second", "third", "lastly",
    "step", "additionally", "furthermore",
}

_DOMAIN_MAP: dict[str, str] = {
    # office
    "docx": "office", "xlsx": "office", "xls": "office",
    "pptx": "office", "pdf": "office", "report": "office",
    "presentation": "office", "document": "office",
    # code
    "code": "code", "script": "code", "program": "code",
    "function": "code", "class": "code", "algorithm": "code",
    "debug": "code", "python": "code",
    # data
    "analyse": "data", "analyze": "data", "statistic": "data", "chart": "data",
    "dataframe": "data", "pandas": "data", "calculate": "data",
    "data": "data", "csv": "data",
    # navigation
    "list": "navigation", "open": "navigation", "search": "navigation",
    "find": "navigation", "show": "navigation",
}

_HEAVY_EXT = {".xlsx", ".xls", ".docx", ".pptx", ".pdf"}
_LIGHT_EXT = {".txt", ".py", ".md", ".csv", ".json", ".log"}


# ── Routing result ─────────────────────────────────────────────

@dataclass
class RouteResult:
    model:   Model
    score:   float          # 0.0 (simple) → 1.0 (complex)
    reason:  str            # human-readable explanation
    domains: Set[str] = field(default_factory=set)


# ── Router ────────────────────────────────────────────────────

class ModelRouter:
    """Complexity heuristic → model selection."""

    BASE_THRESHOLD = 0.28

    def score(self, prompt: str) -> tuple[float, list[str], Set[str]]:
        """Returns (score, reasons, detected domains)."""
        p      = prompt.lower()
        words  = set(re.findall(r"\w+", p))
        score  = 0.0
        reasons: list[str] = []
        domains: Set[str]  = set()

        # ── 1. Prompt length ───────────────────────────────────
        n = len(prompt)
        if n > 200:
            score += 0.25
            reasons.append(f"long ({n}c) +0.25")
        elif n > 80:
            score += 0.12
            reasons.append(f"medium ({n}c) +0.12")

        # ── 2. Heavy keywords ──────────────────────────────────
        heavy_hits = words & _HEAVY
        if heavy_hits:
            delta = min(0.45, len(heavy_hits) * 0.15)
            score += delta
            reasons.append(f"heavy {heavy_hits} +{delta:.2f}")

        # ── 3. Light keywords (negative signal) ───────────────
        light_hits = words & _LIGHT
        if light_hits:
            delta = min(0.25, len(light_hits) * 0.12)
            score -= delta
            reasons.append(f"light {light_hits} -{delta:.2f}")

        # ── 4. Multi-step markers ─────────────────────────────
        ms_hits = words & _MULTISTEP
        if ms_hits:
            score += 0.20
            reasons.append(f"multi-step {ms_hits} +0.20")

        # ── 5. File extensions ─────────────────────────────────
        exts = set(re.findall(r"\.\w{2,5}", p))
        heavy_exts = exts & _HEAVY_EXT
        light_exts = exts & _LIGHT_EXT
        if heavy_exts:
            score += 0.18
            reasons.append(f"heavy ext {heavy_exts} +0.18")
        elif light_exts:
            score -= 0.08
            reasons.append(f"light ext {light_exts} -0.08")

        # ── 6. Inline code snippet ─────────────────────────────
        if re.search(r"\b(def |import |class |```|=>|->)", prompt):
            score += 0.30
            reasons.append("code snippet +0.30")

        # ── 7. Domain detection ───────────────────────────────
        for word, domain in _DOMAIN_MAP.items():
            if word in p:
                domains.add(domain)

        score = round(max(0.0, min(1.0, score)), 3)
        return score, reasons, domains

    def route(self, prompt: str, threshold_adjustment: float = 0.0) -> RouteResult:
        """Returns the optimal model for this prompt.

        Args:
            prompt:               User text.
            threshold_adjustment: (Unused - always returns gemma4:e2b)
        """
        score, reasons, domains = self.score(prompt)
        # Always use e2b as of 2026-04-17
        model: Model = "gemma4:e2b"

        reason = (
            f"gemma4:e2b (score={score}) | "
            + " | ".join(reasons)
        )
        return RouteResult(model=model, score=score,
                           reason=reason, domains=domains)


# ── Singleton ─────────────────────────────────────────────────
_router = ModelRouter()


def route(prompt: str, threshold_adjustment: float = 0.0) -> RouteResult:
    """Public entry point for the router."""
    return _router.route(prompt, threshold_adjustment)
