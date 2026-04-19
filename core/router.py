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
    # Reasoning & analysis (English + French)
    "analyse", "analyze", "analyser", "analysez",
    "compare", "comparison", "comparer", "comparaison",
    "explain", "explique", "expliquer", "explique-moi",
    "summarize", "summarise", "summary", "synthesis", "resume",
    "résume", "résumer", "résumé", "synthèse", "synthétise",
    "interpret", "interprète", "interpréter",
    # Document generation (English + French)
    "generate", "write", "compose",
    "génère", "générer", "rédige", "rédiger",
    "create", "produce",
    "crée", "créer", "écris", "écrire", "produis",
    "report", "presentation", "pptx", "docx", "document",
    "rapport", "présentation",
    # Code (English + French)
    "code", "script", "program", "implement",
    "programme", "implémente", "implémenter",
    "debug", "optimize", "refactor",
    "débogue", "débogage", "optimise",
    "function", "class", "algorithm", "python",
    "fonction", "classe", "algorithme",
    # Data (English + French)
    "calculate", "statistic", "statistics", "chart", "visualize",
    "calcule", "calculer", "calcul", "statistique", "statistiques",
    "graphique", "visualise",
    "pivot", "table", "predict", "model", "regression", "correlation",
    "tableau", "prédis", "modèle", "régression", "corrélation",
    "dataframe", "pandas", "numpy", "average", "mean", "sum",
    "moyenne", "somme",
    "data", "process", "transform",
    "données", "traiter", "traitement", "transformer",
    # Multi-file / batch (English + French)
    "batch", "convert",
    "convertis", "traite",
}

_LIGHT: Set[str] = {
    # Navigation & listing (English + French)
    "list", "show", "display", "open", "which", "what",
    "liste", "lister", "affiche", "montre", "ouvre", "ouvrir",
    "quel", "quelle", "quels",
    "where", "find", "search",
    "où", "trouve", "cherche", "recherche",
    # Simple operations (English + French)
    "copy", "paste", "rename", "move", "delete", "clipboard",
    "copie", "coller", "colle", "renomme", "déplace",
    "supprime", "efface", "presse-papier",
    # Short factual questions (English + French)
    "version", "how many", "date", "time",
    "combien", "heure",
}

_MULTISTEP: Set[str] = {
    # English
    "then", "next", "after", "also", "finally",
    "first", "second", "third", "lastly",
    "step", "additionally", "furthermore",
    # French
    "puis", "ensuite", "après", "enfin",
    "premièrement", "deuxièmement", "d'abord", "finalement",
    "étape", "également", "de plus",
}

_DOMAIN_MAP: dict[str, str] = {
    # office
    "docx": "office", "xlsx": "office", "xls": "office",
    "pptx": "office", "pdf": "office", "report": "office",
    "presentation": "office", "document": "office",
    "rapport": "office", "présentation": "office",
    # code
    "code": "code", "script": "code", "program": "code",
    "function": "code", "class": "code", "algorithm": "code",
    "debug": "code", "python": "code",
    "programme": "code", "fonction": "code", "classe": "code",
    "algorithme": "code", "débogue": "code",
    # data
    "analyse": "data", "analyze": "data", "statistic": "data", "chart": "data",
    "dataframe": "data", "pandas": "data", "calculate": "data",
    "data": "data", "csv": "data",
    "statistique": "data", "graphique": "data", "calcul": "data",
    "données": "data",
    # navigation
    "list": "navigation", "open": "navigation", "search": "navigation",
    "find": "navigation", "show": "navigation",
    "liste": "navigation", "ouvre": "navigation", "cherche": "navigation",
    "trouve": "navigation", "affiche": "navigation",
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
