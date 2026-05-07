"""BISSI v2 backend entrypoint."""

from __future__ import annotations

import logging

import uvicorn

from core.config import DEFAULT_CONFIG
from core.engine import BissiEngine


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Validate llama.cpp runtime and start FastAPI server."""
    engine = BissiEngine(
        model=DEFAULT_CONFIG.llama_cpp.model,
        host=DEFAULT_CONFIG.llama_cpp.host,
        timeout_seconds=DEFAULT_CONFIG.llama_cpp.timeout_seconds,
        max_retries=DEFAULT_CONFIG.llama_cpp.max_retries,
        temperature=DEFAULT_CONFIG.llama_cpp.temperature,
    )

    if not engine.health_check():
        logger.error("llama.cpp server indisponible")
        print(
            "llama.cpp server non disponible.\n"
            "Lance-le avec :\n"
            "  python -m llama_cpp.server\n"
            "    --model <chemin_gguf>\n"
            "    --port 8001\n"
            "    --n_ctx 8192"
        )
        raise SystemExit(1)

    logger.info("BISSI backend ready on http://localhost:8765")
    uvicorn.run(
        "api.server:app",
        host=DEFAULT_CONFIG.server.host,
        port=DEFAULT_CONFIG.server.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
