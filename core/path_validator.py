from pathlib import Path
from typing import Union

ALLOWED_BASE_DIRS = [
    Path.home() / "Documents",
    Path.home() / "Desktop",
    Path.cwd(),
    Path("/tmp"),
]

def is_path_allowed(user_path: Union[str, Path]) -> bool:
    """Vérifie si le chemin est dans un répertoire autorisé (prévention path traversal)."""
    try:
        resolved = Path(user_path).expanduser().resolve()
        for base in ALLOWED_BASE_DIRS:
            try:
                resolved.relative_to(base.resolve())
                return True
            except ValueError:
                continue
        return False
    except Exception:
        return False
