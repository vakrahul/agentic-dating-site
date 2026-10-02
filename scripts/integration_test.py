"""End-to-end API integration test against a throwaway database.

Covers: import -> export roundtrip, import idempotency, rankings (ranks,
badges, breakdown, badge->turn link), pair transcripts, people, SSE snapshot.

Usage: python scripts/integration_test.py
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
PORT = 8017
BASE = f"http://127.0.0.1:{PORT}"
TMP_DB = Path(os.environ.get("TEMP", ".")) / "proxy_integration.db"

FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        print(f"  ok  {message}")
    else:
        print(f" FAIL {message}")
        FAILURES.append(message)


def analysis_payload(i: int) -> dict:
    return {
        "summary": f"Profile summary for person {i}",
        "stated_self": {
            "career": "engineer",
            "ambitions": ["build products"],
            "presentation": "pragmatic",
        },
        "lived_self": {
            "hobbies": ["running", "cooking"],
            "places": ["berlin"],
            "social_energy": "small groups",
            "aesthetic": "minimal",
        },
        "say_do_gap": [
            {
                "stated": "loves travel",
                "lived": "mostly local",
                "type": "diverge",
                "evidence": [{"source": "linkedin", "quote": "love to travel"}],
            }
        ],
        "needs": ["curiosity"],
        "interests": ["design", "ai"],
        "values": ["honesty"],
        "personality": ["direct"],
        "communication_style": "warm but concise",
        "lifestyle": "urban",
        "ambition_level": "high",
        "dating_intent": "long term",
        "looking_for": ["partnership"],
        "dealbreakers": ["dishonesty"],
        "claims": [
            {
                "claim": "works in tech",
                "source": "linkedin",
                "quote": "software engineer at acme",
                "kind": "stated",
                "confidence": 0.9,
            }
        ],
        "overall_confidence": 0.8,
        "data_gaps": ["no hobby posts"],
    }


def build_payload() -> dict:
    people = []
    analyses = []
    for i in range(1, 5):
        people.append(
            {
                "id": i,
                "name": f"Person {i}",
                "linkedin_url": f"https://www.linkedin.com/in/person-{i}",
                "instagram_url": f"https://www.instagram.com/person{i}",
                "status": "analyzed",
                "error": None,
                "linkedin_data": {"headline": f"Person {i} headline"},
                "instagram_data": {"bio": f"bio {i}"},
                "created_at": "2026-10-01T10:00:00+00:00",
            }
        )
        analyses.append(
            {
                "person_id": i,
                "payload": analysis_payload(i),
                "embedding": [0.1 * i, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
                "overall_confidence": 0.8,
                "verified_count": 3,
                "dropped_count": 1,
                "dropped": [{"claim": "unverifiable", "quote": "maybe"}],
            }
        )

    runs = [
        {
            "id": 1,
            "status": "completed",
            "error": None,
            "stats": {"phase": "done", "done": 9, "total": 9, "excluded": []},
            "started_at": "2026-10-01T11:00:00+00:00",
            "finished_at": "2026-10-01T11:20:00+00:00",
        }
    ]

    pair_specs = [
        (1, 2, 95.0, 90.0, 30.0, 83.25),
        (1, 3, 80.0, 78.0, 90.0, 80.7),
        (1, 4, 70.0, 72.0, 60.0, 69.3),
        (2, 3, 74.0, 70.0, 75.0, 72.55),
        (2, 4, 66.0, 68.0, 50.0, 64.4),
        (3, 4, 62.0, 66.0, 40.0, 60.3),
    ]
    round2_pairs = {(1, 2), (1, 3), (3, 4)}
    scenes = [
        "coffee shop",
        "farmers market",
        "bookstore",
        "rooftop",
        "gallery",
        "park bench",
        "night market",
        "record store",
    ]

    dates: list[dict] = []
    turns: list[dict] = []
    agent_scores: list[dict] = []
    referee_scores: list[dict] = []
    pair_scores: list[dict] = []
    date_id = 0

    for rnd in (1, 2):
        for a, b, mutual, ref, emb, final in pair_specs:
            if rnd == 1:
                pass
            elif (a, b) not in round2_pairs:
                continue
            date_id += 1
            turn_count = 8 if rnd == 1 else 12
            dates.append(
                {
                    "id": date_id,
                    "run_id": 1,
                    "round": rnd,
                    "person_a": a,
                    "person_b": b,
                    "scene": scenes[(date_id - 1) % len(scenes)],
                    "moderator_question": "what would you refuse to compromise on?"
                    if rnd == 2
                    else None,
                    "status": "done",
                    "error": None,
                }
            )
            for idx in range(turn_count):
                speaker = a if idx % 2 == 0 else b
                turns.append(
                    {
                        "id": len(turns) + 1,
                        "date_id": date_id,
                        "idx": idx,
                        "speaker_id": speaker,
                        "content": f"turn {idx} from person {speaker} about topic {idx % 3}",
                    }
                )
            for pid in (a, b):
                agent_scores.append(
                    {
                        "id": len(agent_scores) + 1,
                        "date_id": date_id,
                        "person_id": pid,
                        "score": mutual,
                        "chemistry": ref,
                        "shared_interests": ["design"],
                        "friction": ["night owls vs early birds"],
                        "would_meet_again": True,
                        "one_line_for_person": f"sharp and grounded ({pid})",
                    }
                )
            tagged = [
                {"turn_index": 4, "tag": "spark", "reason": "shared vulnerability"},
                {"turn_index": 6, "tag": "friction", "reason": "disagreed on money"},
            ]
            referee_scores.append(
                {
                    "date_id": date_id,
                    "chemistry": ref,
                    "values_fit": min(100.0, ref + 3),
                    "lifestyle_fit": max(0.0, ref - 5),
                    "ambition_fit": ref,
                    "interests_fit": min(100.0, ref + 1),
                    "tagged_turns": tagged,
                }
            )
            if rnd == 2:
                pair_scores.append(
                    {
                        "id": len(pair_scores) + 1,
                        "run_id": 1,
                        "person_a": a,
                        "person_b": b,
                        "date_id": date_id,
                        "round_used": 2,
                        "mutual": mutual,
                        "referee": ref,
                        "embedding": emb,
                        "final": final,
                        "why": "round two chemistry confirmed",
                    }
                )

    r1_date_ids: dict[tuple[int, int], int] = {
        (d["person_a"], d["person_b"]): d["id"] for d in dates if d["round"] == 1
    }
    for a, b, mutual, ref, emb, final in pair_specs:
        if (a, b) in round2_pairs:
            continue
        pair_scores.append(
            {
                "id": len(pair_scores) + 1,
                "run_id": 1,
                "person_a": a,
                "person_b": b,
                "date_id": r1_date_ids[(a, b)],
                "round_used": 1,
                "mutual": mutual,
                "referee": ref,
                "embedding": emb,
                "final": final,
                "why": None,
            }
        )

    return {
        "version": 1,
        "exported_at": "2026-10-01T12:00:00+00:00",
        "people": people,
        "analyses": analyses,
        "runs": runs,
        "dates": dates,
        "turns": turns,
        "agent_scores": agent_scores,
        "referee_scores": referee_scores,
        "pair_scores": pair_scores,
    }


def wait_for_health(client: httpx.Client, timeout: float = 90.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = client.get(f"{BASE}/health", timeout=2.0)
            if resp.status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    return False


def main() -> int:
    for suffix in ("", "-shm", "-wal"):
        p = Path(str(TMP_DB) + suffix)
        if p.exists():
            p.unlink()

    env = dict(os.environ)
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{TMP_DB.as_posix()}"
    server_log = Path(TMP_DB).with_suffix(".log")
    log_fh = open(server_log, "w", encoding="utf-8")  # noqa: SIM115

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", str(ROOT / "backend"), "--port", str(PORT)],
        env=env,
        cwd=str(ROOT),
        stdout=log_fh,
        stderr=subprocess.STDOUT,
    )

    try:
        with httpx.Client(base_url=BASE) as client:
            healthy = wait_for_health(client)
            if not healthy:
                print(" FAIL server never became healthy")
                return 1

            print("== import ==")
            payload = build_payload()
            resp = client.post("/api/import", json={"data": payload}, timeout=30.0)
            check(resp.status_code == 200, f"import status 200 (got {resp.status_code})")
            if resp.status_code != 200:
                log_fh.flush()
                print("--- server log tail ---")
                print("\n".join(server_log.read_text(encoding="utf-8").splitlines()[-40:]))
                return 1
            counts = resp.json().get("imported", {})
            check(counts.get("people") == 4, f"imported 4 people ({counts.get('people')})")
            check(counts.get("dates") == 9, f"imported 9 dates ({counts.get('dates')})")
            check(counts.get("turns") == 84, f"imported 84 turns ({counts.get('turns')})")
            check(counts.get("pair_scores") == 6, f"imported 6 pair scores ({counts.get('pair_scores')})")
            check(counts.get("referee_scores") == 9, f"imported 9 referee scores ({counts.get('referee_scores')})")

            print("== export roundtrip ==")
            first = client.get("/api/export", timeout=30.0).json()
            check(len(first["people"]) == 4, "export has 4 people")
            check(len(first["dates"]) == 9, "export has 9 dates")
            check(len(first["turns"]) == 84, "export has 84 turns")
            check(len(first["pair_scores"]) == 6, "export has 6 pair scores")
            check(
                all(ps.get("date_id") for ps in first["pair_scores"]),
                "all pair scores carry date_id",
            )
            check(
                all(t["content"] == payload["turns"][i]["content"] for i, t in enumerate(first["turns"])),
                "turn contents survive roundtrip",
            )
            exported_person_ids = sorted(p["id"] for p in first["people"])

            print("== idempotency ==")
            again = client.post("/api/import", json={"data": copy.deepcopy(payload)}, timeout=30.0)
            check(again.status_code == 200, "second import 200")
            second = client.get("/api/export", timeout=30.0).json()
            check(len(second["people"]) == 4, "people still 4 after re-import")
            check(len(second["dates"]) == 9, "dates still 9 after re-import")
            check(len(second["turns"]) == 84, "turns still 84 after re-import")
            check(len(second["pair_scores"]) == 6, "pair scores still 6 after re-import")
            check(
                sorted(p["id"] for p in second["people"]) == exported_person_ids,
                "person ids stable across re-import",
            )

            print("== rankings overview ==")
            overview = client.get("/api/rankings", timeout=30.0).json()
            check(len(overview["people"]) == 4, "overview lists 4 analyzed people")
            check(overview["run_id"] is not None, "overview has run_id")

            print("== person ranking ==")
            ranking = client.get("/api/rankings/1", timeout=30.0).json()
            matches = ranking["matches"]
            check(len(matches) == 3, f"person 1 has 3 matches ({len(matches)})")
            check(
                [m["final_rank"] for m in matches] == [1, 2, 3],
                "matches sorted by final rank",
            )
            by_partner = {m["person_id"]: m for m in matches}
            check(set(by_partner) == {2, 3, 4}, "partners are 2,3,4")
            m2 = by_partner.get(2, {})
            check(
                m2.get("similarity_rank") == 3 and m2.get("final_rank") == 1,
                "person1/partner2 sim #3 -> final #1",
            )
            check(m2.get("badge") == "surprise_match", "surprise badge on person1/partner2")
            link = m2.get("badge_turn_link") or {}
            check(
                link.get("turn_index") == 4 and link.get("tag") == "spark",
                f"badge links to spark turn 4 ({link})",
            )
            check(m2.get("pair_href") == "/pair/1/2", "pair_href correct")
            breakdown = m2.get("breakdown") or {}
            check(
                all(k in breakdown for k in ("values", "interests", "lifestyle", "ambition", "chemistry")),
                "breakdown has 5 dims",
            )
            check(breakdown.get("chemistry", 0) > 0, "breakdown chemistry > 0")
            check(
                abs(m2.get("final", 0) - (0.45 * m2.get("mutual", 0) + 0.40 * m2.get("referee", 0) + 0.15 * m2.get("embedding", 0))) < 0.01,
                "final matches weighted formula",
            )

            print("== other rankings ==")
            for pid in (2, 3, 4):
                r = client.get(f"/api/rankings/{pid}", timeout=30.0).json()
                check(len(r["matches"]) == 3, f"person {pid} has 3 matches")
            r2 = client.get("/api/rankings/2", timeout=30.0).json()
            badges = [m["badge"] for m in r2["matches"]]
            check("surprise_match" in badges, "person 2 also gets a surprise badge")

            print("== pair transcript ==")
            pair = client.get("/api/pair/1/2", timeout=30.0).json()
            check(len(pair) == 2, f"pair 1-2 has 2 dates ({len(pair)})")
            check([d["round"] for d in pair] == [1, 2], "rounds ordered 1 then 2")
            r1 = pair[0]
            check(len(r1["turns"]) == 8, "round 1 has 8 turns")
            check(len(pair[1]["turns"]) == 12, "round 2 has 12 turns")
            check(len(r1["agent_scores"]) == 2, "2 agent scores per date")
            check(r1["referee"] is not None, "referee present")
            check(
                len((r1["referee"] or {}).get("tagged_turns", [])) == 2,
                "2 tagged turns",
            )
            check(r1["person_a_name"] == "Person 1", "speaker names resolved")
            check(pair[1]["moderator_question"] is not None, "moderator question on round 2")

            print("== people ==")
            people = client.get("/api/people", timeout=30.0).json()
            check(len(people) == 4, "4 people listed")
            check(all(p["has_analysis"] for p in people), "all have has_analysis")

            print("== SSE snapshot ==")
            try:
                with client.stream("GET", "/api/run/stream", timeout=None) as stream:
                    first_line = ""
                    for line in stream.iter_lines():
                        if line.startswith("data: "):
                            first_line = line
                            break
                snap = json.loads(first_line[len("data: "):])
                check(snap.get("type") == "snapshot", "SSE opens with snapshot")
                check(len(snap.get("people", [])) == 4, "snapshot has 4 people")
            except Exception as exc:  # noqa: BLE001
                check(False, f"SSE snapshot readable ({exc})")

            print("== 404 paths ==")
            check(client.get("/api/rankings/999").status_code == 404, "unknown person 404")
            check(client.get("/api/pair/1/999").status_code == 404, "unknown pair 404")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log_fh.close()
        targets = [
            Path(str(TMP_DB)),
            Path(str(TMP_DB) + "-shm"),
            Path(str(TMP_DB) + "-wal"),
            server_log,
        ]
        for p in targets:
            for _ in range(5):
                try:
                    if p.exists():
                        p.unlink()
                    break
                except PermissionError:
                    time.sleep(0.5)

    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s):")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("\nALL INTEGRATION CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
