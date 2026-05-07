import re
from pathlib import Path
from typing import Union

def validate_path_safety(path: Union[str, Path]):
    """Vérifie qu'un chemin ne contient pas de caractères suspects pour un shell ou ffmpeg."""
    if re.search(r'[;&$`|]', str(path)):
        raise ValueError(f"Chemin de fichier suspect : {path}")
