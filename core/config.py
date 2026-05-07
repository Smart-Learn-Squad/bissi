"""Application-wide configuration for the BISSI v2 backend."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathsConfig:
    """Filesystem paths used by the backend."""

    data_dir: Path = Path("~/.bissi").expanduser()
    profile_path: Path = Path("~/.bissi/profile.json").expanduser()
    conversations_db_path: Path = Path("~/.bissi/conversations.db").expanduser()


@dataclass(frozen=True)
class LlamaCppConfig:
    """llama.cpp runtime parameters."""

    host: str = "http://127.0.0.1:8001"
    model: str = "gemma-4-E2B-it-Q4_K_M"
    timeout_seconds: int = 120
    max_retries: int = 3
    temperature: float = 0.5
    n_ctx: int = 8192


@dataclass(frozen=True)
class AgentConfig:
    """Agent loop settings."""

    max_iterations: int = 7
    context_token_limit: int = 6000


@dataclass(frozen=True)
class ServerConfig:
    """FastAPI backend host and port."""

    host: str = "127.0.0.1"
    port: int = 8765


@dataclass(frozen=True)
class Config:
    """Root immutable configuration object."""

    paths: PathsConfig = PathsConfig()
    llama_cpp: LlamaCppConfig = LlamaCppConfig()
    agent: AgentConfig = AgentConfig()
    server: ServerConfig = ServerConfig()


DEFAULT_CONFIG = Config()
