"""Personalized first greeting generation for onboarding."""

from __future__ import annotations

from core.engine import BissiEngine, BissiEngineError


def generate_greeting(first_name: str, last_name: str, engine: BissiEngine) -> str:
    """Generate a short personalized welcome message via local LLM."""
    prompt = (
        "Tu es BISSI, un assistant IA local. C'est la toute premiere fois "
        f"que tu rencontres {first_name} {last_name}. Genere une salutation "
        "chaleureuse, courte (2-3 phrases max), personnalisee et enthousiaste. "
        "Ne mentionne pas que tu es une IA."
    )
    try:
        response = engine.generate(prompt)
        cleaned = response.strip()
        if cleaned:
            return cleaned
    except BissiEngineError:
        pass
    return f"Bienvenue {first_name} {last_name}. Je suis ravi de commencer avec vous sur cette machine. Dis-moi simplement ce que vous voulez accomplir."
