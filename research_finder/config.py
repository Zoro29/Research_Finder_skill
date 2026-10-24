"""Environment-backed configuration with model-independent defaults."""
from __future__ import annotations
from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    provider: str = "none"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str | None = None
    openalex_mailto: str | None = None
    analysis_mode: str = "online"

    @classmethod
    def from_env(cls) -> "Settings":
        mode = os.getenv("RESEARCH_ANALYSIS_MODE", "online").strip().lower()
        if mode not in {"local", "online"}:
            raise ValueError("RESEARCH_ANALYSIS_MODE must be 'local' or 'online'")
        provider = os.getenv("LLM_PROVIDER", "none").strip().lower()
        if provider not in {"none", "ollama"}:
            raise ValueError("LLM_PROVIDER must be 'none' or 'ollama'")
        base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip().rstrip("/")
        if not base.startswith(("http://", "https://")):
            raise ValueError("OLLAMA_BASE_URL must be an HTTP(S) URL")
        model = os.getenv("OLLAMA_MODEL", "").strip() or None
        if mode == "local" and provider != "ollama":
            raise ValueError("local analysis requires LLM_PROVIDER=ollama")
        if provider == "ollama" and not model:
            raise ValueError("OLLAMA_MODEL is required when LLM_PROVIDER=ollama")
        return cls(
            provider=provider,
            ollama_base_url=base,
            ollama_model=model,
            openalex_mailto=os.getenv("OPENALEX_MAILTO") or None,
            analysis_mode=mode,
        )
