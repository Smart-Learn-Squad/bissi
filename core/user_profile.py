"""UserProfileStore — Mémoire sémantique active pour BISSI.

Enregistre chaque décision de routage pour apprendre le profil
de l'utilisateur et adapter dynamiquement le seuil du router.

Convergence : ~10 requêtes suffisent pour un profil fiable.
Stockage    : JSON léger dans ~/.bissi/user_profile.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Set

from utils.helpers import expand_path, ensure_dir


_DEFAULT_PATH = "~/.bissi/user_profile.json"

_EMPTY_PROFILE: dict = {
    "total_requests": 0,
    "heavy_requests": 0,
    "domains": {},
}

# Nombre minimum de requêtes avant d'activer l'adaptation
_MIN_SAMPLES = 8


class UserProfileStore:
    """Stocke et analyse le comportement de routage de l'utilisateur."""

    def __init__(self, path: str = _DEFAULT_PATH):
        self.path = expand_path(path)
        ensure_dir(self.path.parent)
        self._data = self._load()

    # ── Persistance ────────────────────────────────────────────

    def _load(self) -> dict:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Merge avec le template pour gérer les anciennes versions
                return {**_EMPTY_PROFILE, **data}
            except (json.JSONDecodeError, OSError):
                pass
        return dict(_EMPTY_PROFILE)

    def _save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    # ── Enregistrement ─────────────────────────────────────────

    def record(self, model: str, domains: Set[str]) -> None:
        """Enregistre une décision de routage dans le profil.

        Args:
            model:   Modèle choisi ("gemma4:e2b" ou "gemma4:e4b").
            domains: Ensemble des domaines détectés dans la requête.
        """
        self._data["total_requests"] += 1
        if model == "gemma4:e4b":
            self._data["heavy_requests"] += 1
        for domain in domains:
            self._data["domains"][domain] = (
                self._data["domains"].get(domain, 0) + 1
            )
        self._save()

    # ── Analyse ────────────────────────────────────────────────

    @property
    def heavy_ratio(self) -> float:
        """Ratio de requêtes lourdes. Retourne 0.5 si pas assez de données."""
        total = self._data["total_requests"]
        if total < _MIN_SAMPLES:
            return 0.5  # neutre — pas encore de profil
        return self._data["heavy_requests"] / total

    def threshold_adjustment(self) -> float:
        """Calcule l'ajustement du seuil selon le profil.

        Returns:
            float entre -0.10 et +0.08 :
            - Utilisateur lourd (>65% e4b)  → -0.10 (seuil plus bas)
            - Utilisateur léger (<35% e4b)  → +0.08 (seuil plus haut)
            - Profil mixte ou insuffisant   →  0.00
        """
        if self._data["total_requests"] < _MIN_SAMPLES:
            return 0.0  # pas encore assez de données

        ratio = self.heavy_ratio
        if ratio > 0.65:
            return -0.10
        elif ratio < 0.35:
            return +0.08
        return 0.0

    @property
    def top_domains(self) -> list[tuple[str, int]]:
        """Top 3 domaines par fréquence."""
        return sorted(
            self._data["domains"].items(),
            key=lambda x: -x[1]
        )[:3]

    @property
    def stats(self) -> dict:
        """Résumé lisible du profil pour l'UI."""
        total  = self._data["total_requests"]
        ratio  = self.heavy_ratio
        adj    = self.threshold_adjustment()
        label  = (
            "lourd" if ratio > 0.65
            else "léger" if ratio < 0.35
            else "mixte"
        )
        return {
            "total":       total,
            "heavy_ratio": round(ratio, 2),
            "profile":     label,
            "adjustment":  adj,
            "top_domains": self.top_domains,
            "calibrated":  total >= _MIN_SAMPLES,
        }

    def reset(self) -> None:
        """Remet le profil à zéro."""
        self._data = dict(_EMPTY_PROFILE)
        self._save()


# ── Singleton ─────────────────────────────────────────────────
_profile_store: UserProfileStore | None = None


def get_profile() -> UserProfileStore:
    """Retourne l'instance singleton du profil utilisateur."""
    global _profile_store
    if _profile_store is None:
        _profile_store = UserProfileStore()
    return _profile_store
