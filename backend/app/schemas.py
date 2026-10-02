from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PairInput(BaseModel):
    linkedin_url: str = Field(min_length=1)
    instagram_url: str = Field(min_length=1)
    name: str | None = None

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin(cls, value: str) -> str:
        v = value.strip()
        lowered = v.lower()
        if "linkedin.com/in/" not in lowered:
            raise ValueError("LinkedIn URL must look like https://www.linkedin.com/in/<slug>")
        if not lowered.startswith("http"):
            v = "https://" + v.lstrip("/")
        return v.rstrip("/")

    @field_validator("instagram_url")
    @classmethod
    def validate_instagram(cls, value: str) -> str:
        v = value.strip()
        lowered = v.lower()
        if "instagram.com/" not in lowered:
            raise ValueError("Instagram URL must look like https://www.instagram.com/<handle>")
        if not lowered.startswith("http"):
            v = "https://" + v.lstrip("/")
        return v.rstrip("/")

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        v = value.strip()
        return v or None


class PeopleBatchRequest(BaseModel):
    people: list[PairInput]


class PersonOut(BaseModel):
    id: int
    name: str
    linkedin_url: str
    instagram_url: str
    status: str
    error: str | None = None
    has_analysis: bool = False

    model_config = {"from_attributes": True}


class Evidence(BaseModel):
    source: Literal["linkedin", "instagram"]
    quote: str


class SayDoGap(BaseModel):
    stated: str
    lived: str
    type: Literal["agree", "diverge"]
    evidence: list[Evidence]


class Claim(BaseModel):
    claim: str
    source: Literal["linkedin", "instagram", "both"]
    quote: str
    kind: Literal["stated", "inferred"]
    confidence: float = Field(ge=0.0, le=1.0)


class StatedSelf(BaseModel):
    career: str
    ambitions: list[str] = Field(default_factory=list)
    presentation: str


class LivedSelf(BaseModel):
    hobbies: list[str] = Field(default_factory=list)
    places: list[str] = Field(default_factory=list)
    social_energy: str
    aesthetic: str


class AnalysisPayload(BaseModel):
    summary: str
    stated_self: StatedSelf
    lived_self: LivedSelf
    say_do_gap: list[SayDoGap] = Field(default_factory=list)
    needs: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    personality: list[str] = Field(default_factory=list)
    communication_style: str
    lifestyle: str
    ambition_level: str
    dating_intent: str
    looking_for: list[str] = Field(default_factory=list)
    dealbreakers: list[str] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)
    data_gaps: list[str] = Field(default_factory=list)


class AnalysisOut(BaseModel):
    person_id: int
    payload: AnalysisPayload
    overall_confidence: float
    verified_count: int
    dropped_count: int
    dropped: list[dict] = Field(default_factory=list)
    embedding: list[float] | None = None


class PersonDetailOut(PersonOut):
    linkedin_data: dict | None = None
    instagram_data: dict | None = None
    analysis: AnalysisOut | None = None


class RunOut(BaseModel):
    id: int
    status: str
    error: str | None = None
    stats: dict = Field(default_factory=dict)
    started_at: datetime | None = None
    finished_at: datetime | None = None


class TurnOut(BaseModel):
    idx: int
    speaker_id: int
    speaker_name: str
    content: str


class AgentScoreOut(BaseModel):
    person_id: int
    person_name: str
    score: float
    chemistry: float
    shared_interests: list[str] = Field(default_factory=list)
    friction: list[str] = Field(default_factory=list)
    would_meet_again: bool = False
    one_line_for_person: str | None = None


class RefereeOut(BaseModel):
    chemistry: float
    values_fit: float
    lifestyle_fit: float
    ambition_fit: float
    interests_fit: float
    tagged_turns: list[dict] = Field(default_factory=list)


class PairOut(BaseModel):
    date_id: int
    round: int
    person_a: int
    person_b: int
    person_a_name: str
    person_b_name: str
    scene: str | None = None
    moderator_question: str | None = None
    status: str
    error: str | None = None
    turns: list[TurnOut] = Field(default_factory=list)
    agent_scores: list[AgentScoreOut] = Field(default_factory=list)
    referee: RefereeOut | None = None


class MatchOut(BaseModel):
    person_id: int
    person_name: str
    round_used: int
    final: float
    mutual: float
    referee: float
    embedding: float
    breakdown: dict
    why: str | None = None
    similarity_rank: int
    final_rank: int
    delta: int
    badge: str | None = None
    badge_turn_link: dict | None = None
    pair_href: str
    date_id: int


class RankingOut(BaseModel):
    person: PersonOut
    run_id: int | None
    matches: list[MatchOut] = Field(default_factory=list)
    excluded: list[dict] = Field(default_factory=list)


class RankingsOverviewOut(BaseModel):
    people: list[PersonOut]
    run_id: int | None = None


class ExportOut(BaseModel):
    version: int
    exported_at: datetime
    people: list[dict]
    analyses: list[dict]
    runs: list[dict]
    dates: list[dict]
    turns: list[dict]
    agent_scores: list[dict]
    referee_scores: list[dict]
    pair_scores: list[dict]


class ImportRequest(BaseModel):
    data: ExportOut
