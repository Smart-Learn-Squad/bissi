"""UserProfileStore — Active semantic memory for BISSI.

Records each routing decision to learn the user's profile
and dynamically adapt the router threshold.

Convergence: ~10 requests are sufficient for a reliable profile.
Storage    : Lightweight JSON at ~/.bissi/user_profile.json
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

# Minimum number of requests before enabling adaptation
_MIN_SAMPLES = 8


class UserProfileStore:
    """Stores and analyses the user's routing behaviour."""

    def __init__(self, path: str = _DEFAULT_PATH):
        self.path = expand_path(path)
        ensure_dir(self.path.parent)
        self._data = self._load()

    # ── Persistence ────────────────────────────────────────────

    def _load(self) -> dict:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Merge with template to handle older versions
                return {**_EMPTY_PROFILE, **data}
            except (json.JSONDecodeError, OSError):
                pass
        return dict(_EMPTY_PROFILE)

    def _save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    # ── Recording ──────────────────────────────────────────────

    def record(self, model: str, domains: Set[str]) -> None:
        """Records a routing decision (stub - e2b only as of 2026-04-17).

        Args:
            model:   Model used (always "gemma4:e2b").
            domains: Set of detected domains in the request.
        """
        # As of 2026-04-17, only gemma4:e2b is used.
        # This method is kept for API compatibility but doesn't differentiate.
        self._data["total_requests"] += 1
        for domain in domains:
            self._data["domains"][domain] = (
                self._data["domains"].get(domain, 0) + 1
            )
        self._save()

    # ── Analysis ───────────────────────────────────────────────

    @property
    def heavy_ratio(self) -> float:
        """Ratio of heavy requests (stub - always 0.0 as e2b only)."""
        return 0.0

    def threshold_adjustment(self) -> float:
        """Calculates threshold adjustment (stub - always 0.0 as e2b only).

        Returns:
            Always 0.0 - no adjustment needed with single model.
        """
        return 0.0

    @property
    def top_domains(self) -> list[tuple[str, int]]:
        """Top 3 domains by frequency."""
        return sorted(
            self._data["domains"].items(),
            key=lambda x: -x[1]
        )[:3]

    @property
    def stats(self) -> dict:
        """Readable profile summary for the UI."""
        total  = self._data["total_requests"]
        ratio  = self.heavy_ratio
        adj    = self.threshold_adjustment()
        label  = (
            "heavy" if ratio > 0.65
            else "light" if ratio < 0.35
            else "mixed"
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
        """Reset the profile to empty state."""
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
