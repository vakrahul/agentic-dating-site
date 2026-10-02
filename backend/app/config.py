from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]

LLM_PRESETS: dict[str, dict[str, str]] = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "model_env": "LLM_MODEL",
        "default_model": "gemini-2.5-flash",
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "key_env": "CEREBRAS_API_KEY",
        "model_env": "CEREBRAS_MODEL",
        "default_model": "llama-3.3-70b",
    },
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "gemini"
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    gemini_api_key: str | None = None
    cerebras_api_key: str | None = None
    cerebras_model: str | None = None

    apify_token: str | None = None
    linkedin_actor_id: str = "linkedintel-core/linkedin-profile-scraper-no-cookies"

    database_url: str = f"sqlite+aiosqlite:///{REPO_ROOT / 'proxy.db'}"
    cache_dir: Path = REPO_ROOT / "cache" / "scrape"
    demo_run_path: Path = REPO_ROOT / "demo_run.json"

    scrape_concurrency: int = 4
    analysis_concurrency: int = 1
    date_concurrency: int = 4
    llm_rate_limit_seconds: float = 15.0

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def apify_tokens(self) -> list[str]:
        import os
        tokens: list[str] = []
        if self.apify_token:
            tokens.append(self.apify_token.strip())
        for key, val in os.environ.items():
            if key.upper().startswith("APIFY_TOKEN") and val:
                v = val.strip()
                if v and v not in tokens:
                    tokens.append(v)
        env_file = REPO_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    if k.strip().upper().startswith("APIFY_TOKEN"):
                        val_str = v.strip().strip("'\"")
                        if val_str and val_str not in tokens:
                            tokens.append(val_str)
        return tokens or ([self.apify_token] if self.apify_token else [])

    @property
    def provider_preset(self) -> dict[str, str]:
        return LLM_PRESETS.get(self.llm_provider, LLM_PRESETS["gemini"])

    @property
    def resolved_base_url(self) -> str:
        return self.llm_base_url or self.provider_preset["base_url"]

    @property
    def resolved_api_key(self) -> str:
        if self.llm_api_key:
            return self.llm_api_key
        import os

        preset_key = os.environ.get(self.provider_preset["key_env"], "")
        if preset_key:
            return preset_key
        fallback_env = self.provider_preset["key_env"]
        return getattr(self, fallback_env.lower(), "") or ""

    @property
    def resolved_model(self) -> str:
        if self.llm_model:
            return self.llm_model
        import os

        preset_model_env = self.provider_preset["model_env"]
        return os.environ.get(preset_model_env) or self.provider_preset["default_model"]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    return settings
