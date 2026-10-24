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

    @classmethod
    def from_env(cls) -> "Settings":
        provider = os.getenv("LLM_PROVIDER", "none").strip().lower()
        if provider not in {"none", "ollama"}:
            raise ValueError("LLM_PROVIDER must be 'none' or 'ollama'")
        base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip().rstrip("/")
        if not base.startswith(("http://", "https://")):
            raise ValueError("OLLAMA_BASE_URL must be an HTTP(S) URL")
        model = os.getenv("OLLAMA_MODEL", "").strip() or None
        if provider == "ollama" and not model:
            raise ValueError("OLLAMA_MODEL is required when LLM_PROVIDER=ollama")
        return cls(provider, base, model, os.getenv("OPENALEX_MAILTO") or None)
