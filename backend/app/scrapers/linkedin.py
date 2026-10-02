from __future__ import annotations

from typing import Any

from .linkedin_adapter import adapt, build_input

ACTOR_INPUT_KEY = "profiles"


async def fetch_linkedin(url: str) -> dict[str, Any]:
    from ..config import get_settings
    from .base import ScrapeError, cached_call, get_apify_token

    settings = get_settings()
    token = get_apify_token()

    async def _call() -> dict[str, Any]:
        return await _run_actor(url, settings.linkedin_actor_id, token)

    raw = await cached_call(url, _call)
    normalized = adapt(raw, actor_id=settings.linkedin_actor_id)
    if not normalized.get("name") and not normalized.get("headline"):
        from .base import cache_path
        cache_path(url).unlink(missing_ok=True)
        raise ScrapeError("LinkedIn profile returned no public data")
    return normalized


async def _run_actor(url: str, actor_id: str, token: str) -> dict[str, Any]:
    import asyncio

    from apify_client import ApifyClient

    from .base import ScrapeError

    client = ApifyClient(token)
    actor_input = build_input(url, actor_id)

    def _call() -> dict[str, Any]:
        from datetime import timedelta
        run = client.actor(actor_id).call(run_input=actor_input, wait_duration=timedelta(seconds=180))
        if run is None:
            raise RuntimeError("actor run produced no dataset")
        dataset_id = run.default_dataset_id if hasattr(run, "default_dataset_id") else run.get("defaultDatasetId")
        if not dataset_id:
            raise RuntimeError("actor run produced no dataset")
        items = client.dataset(dataset_id).list_items(clean=True).items
        return {"url": url, "actor_id": actor_id, "items": items}

    try:
        result = await asyncio.to_thread(_call)
    except Exception as exc:  # noqa: BLE001
        raise ScrapeError(f"LinkedIn scrape failed: {exc}") from exc

    items = result.get("items") or []
    if not items:
        raise ScrapeError("LinkedIn profile not found, private, or not public")
    return result
