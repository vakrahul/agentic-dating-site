from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from ..config import get_settings
from ..db import get_session_factory
from ..events import emit
from ..models import (
    AgentScore,
    Analysis,
    Date,
    DateStatus,
    Person,
    PersonStatus,
    RefereeScore,
    Run,
    RunStatus,
    Turn,
)
from ..schemas import AnalysisPayload
from . import prompts
from .calls import (
    DateContext,
    ModeratorQuestion,
    RefereeResult,
    RefereeTag,
    SelfScore,
    TranscriptTurn,
    UnifiedDateResult,
    WhyText,
    generate_turn,
    json_call,
    validate_tags,
)
from .scenes import pick_scene

logger = logging.getLogger(__name__)

_run_tasks: set[asyncio.Task] = set()


def spawn_run(run_id: int, excluded: list[dict]) -> asyncio.Task:
    task = asyncio.create_task(_run_dating(run_id, excluded))
    _run_tasks.add(task)
    task.add_done_callback(_run_tasks.discard)
    return task


class Progress:
    def __init__(self, run_id: int, excluded: list[dict], total_people: int) -> None:
        self.run_id = run_id
        self.lock = asyncio.Lock()
        self.stats: dict[str, Any] = {
            "phase": "starting",
            "total_people": total_people,
            "round1_total": 0,
            "round1_done": 0,
            "round1_failed": 0,
            "round2_total": 0,
            "round2_done": 0,
            "round2_failed": 0,
            "why_total": 0,
            "why_done": 0,
            "excluded": excluded,
        }

    async def set_phase(self, phase: str) -> None:
        async with self.lock:
            self.stats["phase"] = phase
        await self._persist()

    async def bump(self, key: str, *, phase: str | None = None) -> None:
        async with self.lock:
            self.stats[key] = int(self.stats.get(key, 0)) + 1
            if phase:
                self.stats["phase"] = phase
            snapshot = dict(self.stats)
        emit("run.progress", run_id=self.run_id, stats=snapshot)
        await self._persist()

    async def set(self, key: str, value: Any) -> None:
        async with self.lock:
            self.stats[key] = value
            snapshot = dict(self.stats)
        emit("run.progress", run_id=self.run_id, stats=snapshot)
        await self._persist()

    async def _persist(self) -> None:
        async with self.lock:
            snapshot = dict(self.stats)
        factory = get_session_factory()
        async with factory() as session:
            run = await session.get(Run, self.run_id)
            if run is not None:
                run.stats = snapshot
                await session.commit()


async def _run_dating(run_id: int, excluded: list[dict]) -> None:
    factory = get_session_factory()
    settings = get_settings()

    try:
        async with factory() as session:
            people = (
                (
                    await session.execute(
                        select(Person).where(Person.status == PersonStatus.ANALYZED).order_by(Person.id)
                    )
                )
                .scalars()
                .all()
            )
            analyses = {
                row.person_id: row
                for row in (await session.execute(select(Analysis))).scalars().all()
            }

        people = [p for p in people if p.id in analyses]
        if len(people) < 2:
            await _fail_run(run_id, "Need at least 2 analyzed people to start dating")
            return

        payloads = {
            p.id: AnalysisPayload.model_validate(analyses[p.id].payload).model_dump()
            for p in people
        }
        names = {p.id: p.name for p in people}
        embeddings = {p.id: analyses[p.id].embedding for p in people if analyses[p.id].embedding}

        progress = Progress(run_id, excluded, len(people))

        round1_pairs = [
            (people[i].id, people[j].id)
            for i in range(len(people))
            for j in range(i + 1, len(people))
        ]
        await progress.set("round1_total", len(round1_pairs))
        await progress.set_phase("round1")

        dates = await _create_dates(run_id, 1, round1_pairs)
        date_map = {(d.person_a, d.person_b): d.id for d in dates}
        await progress.set("round1_total", len(date_map))

        date_semaphore = asyncio.Semaphore(settings.date_concurrency)
        await asyncio.gather(
            *[
                _run_date_task(
                    date_id,
                    1,
                    a,
                    b,
                    names,
                    payloads,
                    date_semaphore,
                    progress,
                    round_key="round1",
                )
                for (a, b), date_id in date_map.items()
            ]
        )

        if int(progress.stats.get("round1_done", 0)) == 0:
            await _fail_run(run_id, "All Round 1 dates failed")
            return

        round1_scores = await _load_scores(run_id, 1)
        round1_referees = await _load_referees(run_id, 1)
        mutual_r1 = _pair_mutuals(round1_scores, round1_referees)

        top3_pairs = _top3_pairs(mutual_r1, people)
        await progress.set("round2_total", len(top3_pairs))
        await progress.set_phase("round2")

        round2_dates = await _create_dates(run_id, 2, top3_pairs)
        round2_map = {(d.person_a, d.person_b): d.id for d in round2_dates}
        await progress.set("round2_total", len(round2_map))

        if round2_map:
            await asyncio.gather(
                *[
                    _run_date_task(
                        date_id,
                        2,
                        a,
                        b,
                        names,
                        payloads,
                        date_semaphore,
                        progress,
                        round_key="round2",
                    )
                    for (a, b), date_id in round2_map.items()
                ]
            )

        from .scorer import compute_pair_scores, persist_pair_scores

        await progress.set_phase("scoring")
        pair_rows = await compute_pair_scores(
            run_id=run_id,
            people=people,
            payloads=payloads,
            embeddings=embeddings,
        )
        if not pair_rows:
            await _fail_run(run_id, "No pair produced a complete score (all dates failed)")
            return
        await persist_pair_scores(run_id, pair_rows)

        await progress.set("why_total", len(pair_rows))
        await progress.set_phase("why")
        await _generate_why(run_id, pair_rows, progress)

        await progress.set_phase("completed")
        async with factory() as session:
            run = await session.get(Run, run_id)
            if run is not None:
                run.status = RunStatus.COMPLETED
                run.finished_at = datetime.now(timezone.utc)
                stats = dict(run.stats or {})
                stats["phase"] = "completed"
                run.stats = stats
                await session.commit()
        emit("run.status", run_id=run_id, status=RunStatus.COMPLETED, stats=progress.stats)

        try:
            import json
            from ..api.transfer import export_run
            demo_data = await export_run()
            demo_payload = json.loads(demo_data.model_dump_json())
            repo_root = settings.cache_dir.parents[1]
            for target in (repo_root / "demo_run.json", repo_root / "web" / "public" / "demo_run.json"):
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(demo_payload, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info("Auto-exported demo run to demo_run.json and web/public/demo_run.json")
        except Exception:
            logger.exception("Failed to auto-export demo run")

    except Exception as exc:  # noqa: BLE001
        logger.exception("run %s crashed", run_id)
        await _fail_run(run_id, f"Run failed: {exc}")


async def _create_dates(run_id: int, round_no: int, pairs: list[tuple[int, int]]) -> list[Date]:
    factory = get_session_factory()
    async with factory() as session:
        existing = (
            (
                await session.execute(
                    select(Date).where(Date.run_id == run_id, Date.round == round_no)
                )
            )
            .scalars()
            .all()
        )
        have = {(d.person_a, d.person_b) for d in existing} | {
            (d.person_b, d.person_a) for d in existing
        }
        created: list[Date] = []
        for a, b in pairs:
            if (a, b) in have or (b, a) in have:
                continue
            date = Date(
                run_id=run_id,
                round=round_no,
                person_a=a,
                person_b=b,
                status="queued",
            )
            session.add(date)
            created.append(date)
        await session.commit()
        for date in created:
            await session.refresh(date)
        all_dates = (
            (await session.execute(select(Date).where(Date.run_id == run_id, Date.round == round_no)))
            .scalars()
            .all()
        )
        return list(all_dates)


async def _run_date_task(
    date_id: int,
    round_no: int,
    person_a: int,
    person_b: int,
    names: dict[int, str],
    payloads: dict[int, dict],
    semaphore: asyncio.Semaphore,
    progress: Progress,
    round_key: str,
) -> None:
    async with semaphore:
        try:
            await _run_date(
                date_id, round_no, person_a, person_b, names, payloads, progress, round_key
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("date %s failed", date_id)
            await _mark_date_failed(date_id, str(exc))
            await progress.bump(f"{round_key}_failed", phase=round_key)
            emit(
                "date.done",
                date_id=date_id,
                round=round_no,
                person_a=person_a,
                person_b=person_b,
                person_a_name=names.get(person_a, ""),
                person_b_name=names.get(person_b, ""),
                status=DateStatus.FAILED,
                error=str(exc),
            )


async def _run_date(
    date_id: int,
    round_no: int,
    person_a: int,
    person_b: int,
    names: dict[int, str],
    payloads: dict[int, dict],
    progress: Progress,
    round_key: str,
) -> None:
    factory = get_session_factory()
    async with factory() as session:
        date = await session.get(Date, date_id)
        if date is None:
            raise RuntimeError("date row missing")
        date.status = DateStatus.RUNNING
        await session.commit()
        scene = date.scene

    interests_a = list(payloads[person_a].get("interests") or [])
    interests_b = list(payloads[person_b].get("interests") or [])
    if not scene:
        scene = pick_scene(interests_a, interests_b)
        async with factory() as session:
            date = await session.get(Date, date_id)
            if date is not None:
                date.scene = scene
                await session.commit()

    ctx = DateContext(
        person_a=person_a,
        person_b=person_b,
        name_a=names[person_a],
        name_b=names[person_b],
        payload_a=payloads[person_a],
        payload_b=payloads[person_b],
        scene=scene or "a coffee shop",
    )

    system = {
        person_a: prompts.persona_system_prompt(names[person_a], payloads[person_a]),
        person_b: prompts.persona_system_prompt(names[person_b], payloads[person_b]),
    }
    other = {person_a: person_b, person_b: person_a}

    total_turns = 4 if round_no == 1 else 10
    moderator_question: str | None = None
    if round_no == 2:
        try:
            mod = await json_call(
                [
                    {"role": "system", "content": prompts.MODERATOR_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": prompts.moderator_user_prompt(
                            names[person_a], payloads[person_a], names[person_b], payloads[person_b]
                        ),
                    },
                ],
                ModeratorQuestion,
                schema_name="moderator",
                temperature=0.6,
            )
            moderator_question = mod.question.strip()
        except Exception:  # noqa: BLE001
            moderator_question = (
                "When you imagine your next two years, does this person fit into that picture "
                "or not? Say it honestly."
            )
        async with factory() as session:
            date = await session.get(Date, date_id)
            if date is not None:
                date.moderator_question = moderator_question
                await session.commit()

    injected_turn = 5 if round_no == 2 else None
    unified: UnifiedDateResult | None = None
    try:
        mod_q = moderator_question if round_no == 2 else None
        unified = await json_call(
            [
                {"role": "system", "content": prompts.UNIFIED_DATE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": prompts.unified_date_user_prompt(
                        names[person_a],
                        payloads[person_a],
                        names[person_b],
                        payloads[person_b],
                        scene or "a coffee shop",
                        turn_count=total_turns,
                        moderator_question=mod_q,
                    ),
                },
            ],
            UnifiedDateResult,
            schema_name="unified_date",
            temperature=0.6,
        )
    except Exception as exc:
        logger.warning("Unified date LLM call failed (%s); using profile-grounded fallback", exc)
        from .dialogue_synthesizer import synthesize_persona_date

        unified = synthesize_persona_date(
            name_a=names[person_a],
            payload_a=payloads[person_a],
            name_b=names[person_b],
            payload_b=payloads[person_b],
            scene=scene or "a quiet speakeasy",
            round_no=round_no,
            moderator_question=moderator_question,
        )

    # Persist turns
    for idx, t in enumerate(unified.turns[:total_turns]):
        spk = person_a if idx % 2 == 0 else person_b
        async with factory() as session:
            session.add(
                Turn(date_id=date_id, idx=idx, speaker_id=spk, content=t.content)
            )
            await session.commit()

    tagged = validate_tags(unified.referee.tagged_turns, len(unified.turns[:total_turns]))

    async with factory() as session:
        session.add(
            AgentScore(
                date_id=date_id,
                person_id=person_a,
                score=unified.score_a.score,
                chemistry=unified.score_a.chemistry,
                shared_interests=unified.score_a.shared_interests,
                friction=unified.score_a.friction,
                would_meet_again=unified.score_a.would_meet_again,
                one_line_for_person=unified.score_a.one_line_for_person,
            )
        )
        session.add(
            AgentScore(
                date_id=date_id,
                person_id=person_b,
                score=unified.score_b.score,
                chemistry=unified.score_b.chemistry,
                shared_interests=unified.score_b.shared_interests,
                friction=unified.score_b.friction,
                would_meet_again=unified.score_b.would_meet_again,
                one_line_for_person=unified.score_b.one_line_for_person,
            )
        )
        session.add(
            RefereeScore(
                date_id=date_id,
                chemistry=unified.referee.chemistry,
                values_fit=unified.referee.values_fit,
                lifestyle_fit=unified.referee.lifestyle_fit,
                ambition_fit=unified.referee.ambition_fit,
                interests_fit=unified.referee.interests_fit,
                tagged_turns=tagged,
            )
        )
        date = await session.get(Date, date_id)
        if date is not None:
            date.status = DateStatus.DONE
            date.finished_at = datetime.now(timezone.utc)
        await session.commit()

    await progress.bump(f"{round_key}_done", phase=round_key)
    emit(
        "date.done",
        date_id=date_id,
        round=round_no,
        person_a=person_a,
        person_b=person_b,
        person_a_name=names[person_a],
        person_b_name=names[person_b],
        status=DateStatus.DONE,
        scene=scene,
        href=f"/pair/{person_a}/{person_b}",
    )


async def _mark_date_failed(date_id: int, error: str) -> None:
    factory = get_session_factory()
    async with factory() as session:
        date = await session.get(Date, date_id)
        if date is not None:
            date.status = DateStatus.FAILED
            date.error = error[:2000]
            date.finished_at = datetime.now(timezone.utc)
            await session.commit()


async def _load_scores(run_id: int, round_no: int) -> dict[int, dict[int, float]]:
    factory = get_session_factory()
    async with factory() as session:
        rows = (
            (
                await session.execute(
                    select(AgentScore, Date)
                    .join(Date, Date.id == AgentScore.date_id)
                    .where(Date.run_id == run_id, Date.round == round_no, Date.status == DateStatus.DONE)
                )
            )
            .all()
        )
    out: dict[int, dict[int, float]] = {}
    for score, date in rows:
        partner = date.person_b if score.person_id == date.person_a else date.person_a
        out.setdefault(score.person_id, {})[partner] = float(score.score)
    return out


async def _load_referees(run_id: int, round_no: int) -> dict[tuple[int, int], dict]:
    factory = get_session_factory()
    async with factory() as session:
        rows = (
            (
                await session.execute(
                    select(RefereeScore, Date)
                    .join(Date, Date.id == RefereeScore.date_id)
                    .where(Date.run_id == run_id, Date.round == round_no, Date.status == DateStatus.DONE)
                )
            )
            .all()
        )
    out: dict[tuple[int, int], dict] = {}
    for referee, date in rows:
        key = tuple(sorted((date.person_a, date.person_b)))
        out[key] = {
            "chemistry": referee.chemistry,
            "values_fit": referee.values_fit,
            "lifestyle_fit": referee.lifestyle_fit,
            "ambition_fit": referee.ambition_fit,
            "interests_fit": referee.interests_fit,
            "tagged_turns": referee.tagged_turns or [],
            "date_id": date.id,
            "round": date.round,
        }
    return out


def _pair_mutuals(
    scores: dict[int, dict[int, float]], referees: dict[tuple[int, int], dict]
) -> dict[tuple[int, int], float]:
    from ..scoring.normalize import z_normalize

    normalized: dict[int, dict[int, float]] = {}
    for person_id, partner_scores in scores.items():
        values = list(partner_scores.values())
        scaled = z_normalize(values)
        normalized[person_id] = dict(zip(partner_scores.keys(), scaled))

    out: dict[tuple[int, int], float] = {}
    for person_id, partner_scores in normalized.items():
        for partner, value in partner_scores.items():
            key = tuple(sorted((person_id, partner)))
            if key in out:
                continue
            other = normalized.get(partner, {}).get(person_id)
            if other is None:
                continue
            from ..scoring.composite import geometric_mean

            out[key] = geometric_mean(value, other)
    return out


def _top3_pairs(
    mutual_r1: dict[tuple[int, int], float], people: list[Person]
) -> list[tuple[int, int]]:
    by_person: dict[int, list[tuple[int, float]]] = {}
    for (a, b), value in mutual_r1.items():
        by_person.setdefault(a, []).append((b, value))
        by_person.setdefault(b, []).append((a, value))
    selected: set[tuple[int, int]] = set()
    for person in people:
        partners = sorted(by_person.get(person.id, []), key=lambda t: (-t[1], t[0]))
        for partner, _value in partners[:3]:
            selected.add(tuple(sorted((person.id, partner))))
    return sorted(selected)


async def _generate_why(
    run_id: int, pair_rows: list[dict[str, Any]], progress: Progress
) -> None:
    settings = get_settings()
    semaphore = asyncio.Semaphore(settings.date_concurrency)
    factory = get_session_factory()

    async def one(row: dict[str, Any]) -> None:
        async with semaphore:
            date_id = row["date_id"]
            try:
                async with factory() as session:
                    turns = (
                        (
                            await session.execute(
                                select(Turn).where(Turn.date_id == date_id).order_by(Turn.idx)
                            )
                        )
                        .scalars()
                        .all()
                    )
                    referee = await session.get(RefereeScore, date_id)
                transcript = "\n".join(
                    f"[turn {t.idx}] {row_names(row, t.speaker_id)}: {t.content}" for t in turns
                )
                referee_block = {
                    "chemistry": referee.chemistry,
                    "values_fit": referee.values_fit,
                    "lifestyle_fit": referee.lifestyle_fit,
                    "ambition_fit": referee.ambition_fit,
                    "interests_fit": referee.interests_fit,
                    "tagged_turns": referee.tagged_turns or [],
                }
                result = await json_call(
                    [
                        {"role": "system", "content": prompts.WHY_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": prompts.why_user_prompt(transcript, referee_block),
                        },
                    ],
                    WhyText,
                    schema_name="why",
                    temperature=0.3,
                    max_tokens=600,
                )
                why = result.why.strip()
                if not any(ch.isdigit() for ch in why):
                    raise ValueError("why text did not cite a turn number")
            except Exception:  # noqa: BLE001 - deterministic fallback from tags only
                why = _fallback_why(row)

            async with factory() as session:
                from ..models import PairScore

                pair = (
                    (
                        await session.execute(
                            select(PairScore).where(
                                PairScore.run_id == run_id,
                                PairScore.person_a == row["person_a"],
                                PairScore.person_b == row["person_b"],
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if pair is not None:
                    pair.why = why
                    await session.commit()
            await progress.bump("why_done", phase="why")

    await asyncio.gather(*[one(row) for row in pair_rows])


def row_names(row: dict[str, Any], person_id: int) -> str:
    if person_id == row["person_a"]:
        return row["name_a"]
    if person_id == row["person_b"]:
        return row["name_b"]
    return f"person {person_id}"


def _fallback_why(row: dict[str, Any]) -> str:
    tags = row.get("tagged_turns") or []
    if not tags:
        return (
            f"No referee-tagged turns decided this date. Referee dimensions: "
            f"values {row['breakdown']['values']}, lifestyle {row['breakdown']['lifestyle']}, "
            f"chemistry {row['breakdown']['chemistry']} (see the transcript for detail)."
        )
    parts = []
    for tag in tags[:2]:
        label = "Sparked at" if tag.get("tag") == "spark" else "Friction at"
        parts.append(f"{label} turn {int(tag.get('turn_index', 0)) + 1}: {tag.get('reason', '')}")
    return " ".join(parts)


async def _fail_run(run_id: int, error: str) -> None:
    factory = get_session_factory()
    async with factory() as session:
        run = await session.get(Run, run_id)
        if run is not None:
            run.status = RunStatus.FAILED
            run.error = error
            run.finished_at = datetime.now(timezone.utc)
            await session.commit()
    emit("run.status", run_id=run_id, status=RunStatus.FAILED, error=error)
