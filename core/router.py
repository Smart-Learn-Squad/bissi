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
    # Raisonnement & analyse
    "analyse", "analyser", "analysez", "analyse-moi",
    "compare", "comparer", "comparaison",
    "explique", "expliquer", "explique-moi",
    "résume", "résumer", "résumé", "synthèse", "synthétise",
    "interprète", "interpréter",
    # Génération de documents
    "génère", "générer", "rédige", "rédiger", "compose",
    "crée", "créer", "écris", "écrire", "produis",
    "rapport", "présentation", "pptx", "docx", "document",
    # Code
    "code", "script", "programme", "implémente", "implémenter",
    "débogue", "débogage", "optimise", "refactor",
    "fonction", "classe", "algorithme", "python",
    # Data
    "calcule", "calculer", "calcul", "statistique", "statistiques",
    "graphique", "visualise", "pivot", "tableau",
    "prédis", "modèle", "régression", "corrélation",
    "dataframe", "pandas", "numpy", "moyenne", "somme",
    "données", "traiter", "traitement", "transformer",
    # Multi-fichiers / batch
    "tous les fichiers", "chaque fichier", "batch",
    "convertis", "traite",
}

_LIGHT: Set[str] = {
    # Navigation & listing
    "liste", "lister", "listez", "affiche", "montre",
    "ouvre", "ouvrir", "quel", "quelle", "quels",
    "où", "trouve", "cherche", "recherche",
    # Opérations simples
    "copie", "coller", "colle", "renomme", "déplace",
    "supprime", "efface", "clipboard", "presse-papier",
    # Questions factuelles courtes
    "c'est quoi", "qu'est-ce", "version", "quel est",
    "combien", "date", "heure",
}

_MULTISTEP: Set[str] = {
    "puis", "ensuite", "après", "et aussi", "enfin",
    "premièrement", "deuxièmement", "d'abord", "finalement",
    "étape", "step", "ensuite", "également", "de plus",
}

_DOMAIN_MAP: dict[str, str] = {
    # office
    "docx": "office", "xlsx": "office", "xls": "office",
    "pptx": "office", "pdf": "office", "rapport": "office",
    "présentation": "office", "document": "office",
    # code
    "code": "code", "script": "code", "programme": "code",
    "fonction": "code", "classe": "code", "algorithme": "code",
    "débogue": "code", "python": "code",
    # data
    "analyse": "data", "statistique": "data", "graphique": "data",
    "dataframe": "data", "pandas": "data", "calcul": "data",
    "données": "data", "csv": "data",
    # navigation
    "liste": "navigation", "ouvre": "navigation", "cherche": "navigation",
    "trouve": "navigation", "affiche": "navigation",
}

_HEAVY_EXT = {".xlsx", ".xls", ".docx", ".pptx", ".pdf"}
_LIGHT_EXT = {".txt", ".py", ".md", ".csv", ".json", ".log"}


# ── Résultat du routage ────────────────────────────────────────

@dataclass
class RouteResult:
    model:   Model
    score:   float          # 0.0 (simple) → 1.0 (complexe)
    reason:  str            # explication lisible
    domains: Set[str] = field(default_factory=set)


# ── Router ────────────────────────────────────────────────────

class ModelRouter:
    """Heuristique de complexité → sélection de modèle."""

    BASE_THRESHOLD = 0.28

    def score(self, prompt: str) -> tuple[float, list[str], Set[str]]:
        """Retourne (score, raisons, domaines détectés)."""
        p      = prompt.lower()
        words  = set(re.findall(r"\w+", p))
        score  = 0.0
        reasons: list[str] = []
        domains: Set[str]  = set()

        # ── 1. Longueur du prompt ──────────────────────────────
        n = len(prompt)
        if n > 200:
            score += 0.25
            reasons.append(f"long ({n}c) +0.25")
        elif n > 80:
            score += 0.12
            reasons.append(f"moyen ({n}c) +0.12")

        # ── 2. Mots-clés lourds ────────────────────────────────
        heavy_hits = words & _HEAVY
        if heavy_hits:
            delta = min(0.45, len(heavy_hits) * 0.15)
            score += delta
            reasons.append(f"lourd {heavy_hits} +{delta:.2f}")

        # ── 3. Mots-clés légers (signal négatif) ──────────────
        light_hits = words & _LIGHT
        if light_hits:
            delta = min(0.25, len(light_hits) * 0.12)
            score -= delta
            reasons.append(f"léger {light_hits} -{delta:.2f}")

        # ── 4. Marqueurs multi-étapes ─────────────────────────
        ms_hits = words & _MULTISTEP
        if ms_hits:
            score += 0.20
            reasons.append(f"multi-étapes {ms_hits} +0.20")

        # ── 5. Extensions fichiers ─────────────────────────────
        exts = set(re.findall(r"\.\w{2,5}", p))
        heavy_exts = exts & _HEAVY_EXT
        light_exts = exts & _LIGHT_EXT
        if heavy_exts:
            score += 0.18
            reasons.append(f"ext lourde {heavy_exts} +0.18")
        elif light_exts:
            score -= 0.08
            reasons.append(f"ext légère {light_exts} -0.08")

        # ── 6. Snippet de code inline ─────────────────────────
        if re.search(r"\b(def |import |class |```|=>|->)", prompt):
            score += 0.30
            reasons.append("snippet code +0.30")

        # ── 7. Détection des domaines ─────────────────────────
        for word, domain in _DOMAIN_MAP.items():
            if word in p:
                domains.add(domain)

        score = round(max(0.0, min(1.0, score)), 3)
        return score, reasons, domains

    def route(self, prompt: str, threshold_adjustment: float = 0.0) -> RouteResult:
        """Retourne le modèle optimal pour ce prompt.

        Args:
            prompt:               Texte de l'utilisateur.
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
    """Point d'entrée public du router."""
    return _router.route(prompt, threshold_adjustment)
