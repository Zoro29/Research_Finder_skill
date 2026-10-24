"""Environment-backed configuration with model-independent defaults."""
from __future__ import annotations
from dataclasses import dataclass
import os
from pathlib import Path

def _load_dotenv() -> None:
    path = Path.cwd() / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))

@dataclass(frozen=True)
class Settings:
    provider: str = "none"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str | None = None
    openalex_mailto: str | None = None
    analysis_mode: str = "online"
    ollama_timeout: float = 180.0
    ollama_num_predict: int = 512

    @classmethod
    def from_env(cls, load_dotenv: bool = False) -> "Settings":
        if load_dotenv:
            _load_dotenv()
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
        try:
            timeout = float(os.getenv("OLLAMA_TIMEOUT", "180"))
            num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", "512"))
        except ValueError as exc:
            raise ValueError("OLLAMA_TIMEOUT must be a number and OLLAMA_NUM_PREDICT an integer") from exc
        if timeout <= 0 or num_predict <= 0:
            raise ValueError("OLLAMA_TIMEOUT and OLLAMA_NUM_PREDICT must be positive")
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
            ollama_timeout=timeout,
            ollama_num_predict=num_predict,
        )
