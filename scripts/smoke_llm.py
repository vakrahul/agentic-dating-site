from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.config import get_settings  # noqa: E402
from app.llm import raw_json_call  # noqa: E402


async def main() -> None:
    settings = get_settings()
    print(f"provider={settings.llm_provider} base={settings.resolved_base_url} model={settings.resolved_model}")
    if not settings.resolved_api_key:
        print("LLM FAILED: no api key resolved")
        return
    try:
        out = await raw_json_call(
            [
                {"role": "system", "content": "Respond with JSON only."},
                {"role": "user", "content": 'Return the JSON object {"ok": true} exactly.'},
            ],
            schema_name="smoke",
            max_tokens=64,
        )
        print("LLM OK:", out)
    except Exception as exc:  # noqa: BLE001
        print("LLM FAILED:", type(exc).__name__, str(exc)[:600])


if __name__ == "__main__":
    asyncio.run(main())
