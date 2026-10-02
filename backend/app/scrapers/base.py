from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Awaitable, Callable

from ..config import get_settings


class ScrapeError(Exception):
    """Raised when a scrape cannot produce usable public data."""


_token_idx = 0


def get_apify_token() -> str:
    global _token_idx
    settings = get_settings()
    tokens = settings.apify_tokens
    if not tokens:
        raise ScrapeError("No APIFY_TOKEN configured in .env")
    token = tokens[_token_idx % len(tokens)]
    _token_idx += 1
    return token


def cache_key(url: str) -> str:
    normalized = url.strip().lower().rstrip("/")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def cache_path(url: str) -> Path:
    settings = get_settings()
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    return settings.cache_dir / f"{cache_key(url)}.json"


def read_cache(url: str) -> dict[str, Any] | None:
    path = cache_path(url)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_cache(url: str, payload: dict[str, Any]) -> None:
    path = cache_path(url)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


async def cached_call(url: str, fetcher: Callable[[], Awaitable[dict[str, Any]]]) -> dict[str, Any]:
    cached = read_cache(url)
    if cached is not None:
        return cached
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            payload = await fetcher()
            write_cache(url, payload)
            return payload
        except ScrapeError:
            raise
        except Exception as exc:  # noqa: BLE001 - retry once then surface
            last_error = exc
            if attempt == 1:
                raise ScrapeError(f"{type(exc).__name__}: {exc}") from exc
    raise ScrapeError(str(last_error) if last_error else "unknown scrape failure")
