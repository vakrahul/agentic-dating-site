from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from ..llm import raw_json_call
from . import prompts

logger = logging.getLogger(__name__)


class SelfScore(BaseModel):
    score: float = Field(ge=0, le=100)
    chemistry: float = Field(ge=0, le=100)
    shared_interests: list[str] = Field(default_factory=list)
    friction: list[str] = Field(default_factory=list)
    would_meet_again: bool = False
    one_line_for_person: str = ""


class RefereeTag(BaseModel):
    turn_index: int = Field(ge=0)
    tag: str
    reason: str


class RefereeResult(BaseModel):
    chemistry: float = Field(ge=0, le=100)
    values_fit: float = Field(ge=0, le=100)
    lifestyle_fit: float = Field(ge=0, le=100)
    ambition_fit: float = Field(ge=0, le=100)
    interests_fit: float = Field(ge=0, le=100)
    tagged_turns: list[RefereeTag] = Field(default_factory=list)


class ModeratorQuestion(BaseModel):
    category: str
    question: str


class WhyText(BaseModel):
    why: str = Field(min_length=1)


class UnifiedTurn(BaseModel):
    speaker: str
    content: str


class UnifiedDateResult(BaseModel):
    turns: list[UnifiedTurn] = Field(default_factory=list)
    score_a: SelfScore
    score_b: SelfScore
    referee: RefereeResult


@dataclass
class TranscriptTurn:
    idx: int
    speaker_id: int
    speaker_name: str
    content: str

    def line(self) -> str:
        return f"[turn {self.idx}] {self.speaker_name}: {self.content}"


@dataclass
class DateContext:
    person_a: int
    person_b: int
    name_a: str
    name_b: str
    payload_a: dict
    payload_b: dict
    scene: str
    turns: list[TranscriptTurn] = field(default_factory=list)

    def transcript(self) -> str:
        return "\n".join(t.line() for t in self.turns)


async def json_call(
    messages: list[dict],
    model_cls: type[BaseModel],
    *,
    schema_name: str,
    temperature: float = 0.5,
    max_tokens: int = 2048,
) -> BaseModel:
    """JSON mode call with validation and exactly one retry on failure."""
    last_error: Exception | None = None
    attempt_messages = list(messages)
    for attempt in range(2):
        raw = await raw_json_call(
            attempt_messages,
            schema_name=schema_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        try:
            data = json.loads(raw)
            return model_cls.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            if attempt == 0:
                attempt_messages = messages + [
                    {"role": "assistant", "content": raw[:4000]},
                    {
                        "role": "user",
                        "content": (
                            f"Your response failed validation: {exc}. "
                            "Return a corrected JSON object only, no prose."
                        ),
                    },
                ]
                continue
    raise RuntimeError(f"{schema_name} failed validation twice: {last_error}")


async def generate_turn(
    system: str,
    history: list[tuple[str, str, str]],
    prompt: str,
) -> str:
    """history: list of (role_for_this_speaker, speaker_name, content)."""
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    for role, _name, content in history:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": prompt})
    from ..llm import raw_text_call
    return await raw_text_call(messages, temperature=0.8, max_tokens=256)


def validate_tags(tags: list[RefereeTag], turn_count: int) -> list[dict[str, Any]]:
    valid: list[dict[str, Any]] = []
    for tag in tags:
        if tag.tag not in ("spark", "friction"):
            continue
        if tag.turn_index >= turn_count:
            continue
        valid.append(
            {"turn_index": tag.turn_index, "tag": tag.tag, "reason": tag.reason}
        )
    valid.sort(key=lambda t: t["turn_index"])
    return valid
