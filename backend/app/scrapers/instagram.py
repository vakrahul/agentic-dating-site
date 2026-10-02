from __future__ import annotations

from typing import Any

from ..config import get_settings
from .base import ScrapeError, cached_call

ACTOR_ID = "apify/instagram-profile-scraper"


def extract_handle(url: str) -> str:
    cleaned = url.strip().rstrip("/")
    if "/" in cleaned.split("//", 1)[-1]:
        parts = cleaned.split("//", 1)[-1].split("/")
        for part in parts[1:]:
            if part and part not in ("p", "reel", "tv"):
                return part
    return cleaned.split("/")[-1]


async def fetch_instagram(url: str) -> dict[str, Any]:
    from .base import get_apify_token

    token = get_apify_token()

    async def _call() -> dict[str, Any]:
        return await _run_actor(url, token)

    return await cached_call(url, _call)


async def _run_actor(url: str, token: str) -> dict[str, Any]:
    import asyncio

    from apify_client import ApifyClient

    handle = extract_handle(url)
    client = ApifyClient(token)

    def _call() -> dict[str, Any]:
        from datetime import timedelta
        run = client.actor(ACTOR_ID).call(
            run_input={"usernames": [handle], "resultsLimit": 5},
            wait_duration=timedelta(seconds=180),
        )
        if run is None:
            raise RuntimeError("actor run produced no dataset")
        dataset_id = run.default_dataset_id if hasattr(run, "default_dataset_id") else run.get("defaultDatasetId")
        if not dataset_id:
            raise RuntimeError("actor run produced no dataset")
        items = client.dataset(dataset_id).list_items(clean=True).items
        return {"handle": handle, "items": items}

    try:
        result = await asyncio.to_thread(_call)
    except Exception as exc:  # noqa: BLE001
        raise ScrapeError(f"Instagram scrape failed: {exc}") from exc

    items = result.get("items") or []
    if not items:
        raise ScrapeError("Instagram profile not found or not public")
    item = items[0]
    ig_status = item.get("ig_status")
    if ig_status and ig_status != "ok":
        raise ScrapeError(_status_error(ig_status, result["handle"]))
    if item.get("is_private"):
        raise ScrapeError("Private Instagram account")

    return {
        "source": "instagram",
        "username": item.get("username") or result["handle"],
        "full_name": item.get("full_name"),
        "biography": item.get("biography") or "",
        "external_url": item.get("external_url"),
        "followers": item.get("followers"),
        "following": item.get("following"),
        "post_count": item.get("post_count"),
        "is_verified": bool(item.get("is_verified")),
        "is_private": bool(item.get("is_private")),
        "category": item.get("category"),
        "latest_posts": _normalize_posts(item.get("latest_posts") or item.get("latestPosts") or []),
    }


def _status_error(status: str, handle: str) -> str:
    if status == "not_found":
        return f"Instagram profile @{handle} not found (private or removed)"
    if status == "invalid_input":
        return f"Invalid Instagram URL for @{handle}"
    return f"Instagram scrape status: {status}"


def _normalize_posts(posts: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for post in posts:
        if not isinstance(post, dict):
            continue
        caption = post.get("caption")
        if isinstance(caption, dict):
            caption = caption.get("text") or ""
        caption = caption or ""
        hashtags = post.get("hashtags")
        if not hashtags:
            hashtags = [
                word.lstrip("#")
                for word in caption.split()
                if word.startswith("#") and len(word) > 1
            ]
        out.append(
            {
                "caption": caption,
                "hashtags": hashtags or [],
                "taken_at": post.get("taken_at") or post.get("taken_at_timestamp"),
                "url": post.get("url"),
                "likes": post.get("likesCount", post.get("likes_count")),
                "comments": post.get("commentsCount", post.get("comments_count")),
            }
        )
    return out[:12]
