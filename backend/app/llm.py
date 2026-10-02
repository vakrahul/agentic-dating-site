from __future__ import annotations

import asyncio
from functools import lru_cache
import logging
import re
from typing import Any

from openai import AsyncOpenAI

from .config import get_settings

logger = logging.getLogger(__name__)

_rate_limit_lock = asyncio.Lock()
_last_call_time: float = 0.0

DEFAULT_INTERVAL_SECONDS = 15.0


@lru_cache
def get_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(
        api_key=settings.resolved_api_key,
        base_url=settings.resolved_base_url,
        timeout=120.0,
        max_retries=1,
    )


async def _rate_limited_completion(
    messages: list[dict],
    *,
    temperature: float,
    max_tokens: int,
    response_format: dict[str, Any] | None = None,
    max_attempts: int = 1,
) -> str:
    global _last_call_time

    client = get_client()
    settings = get_settings()
    min_interval = float(getattr(settings, "llm_rate_limit_seconds", DEFAULT_INTERVAL_SECONDS))

    for attempt in range(max_attempts):
        # 1. Enforce minimum interval spacing between calls (15 - 30 seconds)
        async with _rate_limit_lock:
            loop = asyncio.get_running_loop()
            now = loop.time()
            elapsed = now - _last_call_time
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                logger.info("Rate limiter: waiting %.1fs before next LLM request...", wait_time)
                await asyncio.sleep(wait_time)
            _last_call_time = loop.time()

        # 2. Make the API call
        try:
            kwargs: dict[str, Any] = {
                "model": settings.resolved_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max(max_tokens, 256),
            }
            if response_format:
                kwargs["response_format"] = response_format

            completion = await client.chat.completions.create(**kwargs)
            content = completion.choices[0].message.content or ""
            return content

        except Exception as exc:
            err_str = str(exc)
            is_429 = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()
            if is_429 and attempt < max_attempts - 1:
                # Extract suggested retry delay or use 20-30s
                delay = 20.0
                match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_str, re.IGNORECASE)
                if match:
                    delay = max(float(match.group(1)) + 2.0, 15.0)
                logger.warning(
                    "LLM 429 quota hit. Sleeping %.1fs before retry (attempt %d/%d)...",
                    delay,
                    attempt + 1,
                    max_attempts,
                )
                await asyncio.sleep(delay)
                continue
            raise


async def raw_json_call(
    messages: list[dict],
    *,
    schema_name: str,
    temperature: float = 0.4,
    max_tokens: int = 4096,
) -> str:
    content = await _rate_limited_completion(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    if not content.strip():
        raise ValueError(f"{schema_name}: empty LLM response")
    return content


async def raw_text_call(
    messages: list[dict],
    *,
    temperature: float = 0.8,
    max_tokens: int = 256,
) -> str:
    content = await _rate_limited_completion(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=None,
    )
    if not content.strip():
        raise ValueError("empty LLM response")
    return content.strip()
