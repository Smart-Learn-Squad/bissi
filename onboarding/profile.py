"""First-launch user profile persistence for BISSI."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from core.config import DEFAULT_CONFIG


def is_first_launch() -> bool:
    """Return True when no local user profile exists yet."""
    return not DEFAULT_CONFIG.paths.profile_path.exists()


def save_profile(
    first_name: Union[str, Dict[str, Any]],
    last_name: Optional[str] = None,
    language: str = "fr",
) -> None:
    """Persist user profile payload on local disk.

    Supports both legacy positional args and dict payload usage:
    - save_profile("Jane", "Doe", "fr")
    - save_profile({"name": "Jane Doe", "language": "fr", "tone": "pro"})
    """
    profile_path = DEFAULT_CONFIG.paths.profile_path
    profile_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(first_name, dict):
        incoming = dict(first_name)
        full_name = str(incoming.get("name", "")).strip()
        first = str(incoming.get("first_name", "")).strip()
        last = str(incoming.get("last_name", "")).strip()
        if not first and full_name:
            parts = full_name.split(maxsplit=1)
            first = parts[0]
            last = parts[1] if len(parts) > 1 else ""
        payload = {
            "first_name": first,
            "last_name": last,
            "name": f"{first} {last}".strip() if (first or last) else full_name,
            "language": str(incoming.get("language", language)),
            "tone": incoming.get("tone"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    else:
        first = first_name.strip()
        last = (last_name or "").strip()
        payload = {
            "first_name": first,
            "last_name": last,
            "name": f"{first} {last}".strip(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "language": language,
        }

    profile_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_profile() -> Optional[Dict[str, Any]]:
    """Load local user profile if present and valid."""
    profile_path = DEFAULT_CONFIG.paths.profile_path
    if not profile_path.exists():
        return None
    try:
        return json.loads(profile_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
