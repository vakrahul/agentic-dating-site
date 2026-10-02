"""Load the synthetic integration fixture into a running server's DB.

Development/demo convenience only — the data is fabricated (Person 1..4).
Wipe the database and delete web/public/demo_run.json before a real run.

Usage: python scripts/load_fixture.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from integration_test import build_payload  # noqa: E402

BASE = "http://127.0.0.1:8000"


def main() -> int:
    payload = build_payload()
    with httpx.Client(base_url=BASE, timeout=60.0) as client:
        try:
            client.get("/health")
        except httpx.HTTPError:
            print("backend not reachable at " + BASE)
            return 1

        resp = client.post("/api/import", json={"data": payload})
        resp.raise_for_status()
        print("imported:", resp.json()["imported"])

        exported = client.get("/api/export")
        exported.raise_for_status()
        data = exported.json()

    target = ROOT / "web" / "public" / "demo_run.json"
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {target} ({len(data['dates'])} dates, {len(data['pair_scores'])} pair scores)")
    print("fixture loaded — open http://localhost:3000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
