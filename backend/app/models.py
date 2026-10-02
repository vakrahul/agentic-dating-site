from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class PersonStatus:
    QUEUED = "queued"
    SCRAPING = "scraping"
    SCRAPED = "scraped"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class RunStatus:
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DateStatus:
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    linkedin_url: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    instagram_url: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=PersonStatus.QUEUED, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    instagram_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Analysis(Base):
    __tablename__ = "analyses"

    person_id: Mapped[int] = mapped_column(
        ForeignKey("people.id", ondelete="CASCADE"), primary_key=True
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    overall_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    verified_count: Mapped[int] = mapped_column(Integer, default=0)
    dropped_count: Mapped[int] = mapped_column(Integer, default=0)
    dropped: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(32), default=RunStatus.RUNNING, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    stats: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Date(Base):
    __tablename__ = "dates"
    __table_args__ = (
        UniqueConstraint("run_id", "round", "person_a", "person_b", name="uq_date_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    person_a: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    person_b: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    scene: Mapped[str | None] = mapped_column(String(255), nullable=True)
    moderator_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=DateStatus.RUNNING, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Turn(Base):
    __tablename__ = "turns"
    __table_args__ = (UniqueConstraint("date_id", "idx", name="uq_turn_idx"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date_id: Mapped[int] = mapped_column(ForeignKey("dates.id", ondelete="CASCADE"), nullable=False)
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker_id: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class AgentScore(Base):
    __tablename__ = "agent_scores"
    __table_args__ = (UniqueConstraint("date_id", "person_id", name="uq_agent_score"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date_id: Mapped[int] = mapped_column(ForeignKey("dates.id", ondelete="CASCADE"), nullable=False)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    chemistry: Mapped[float] = mapped_column(Float, default=0.0)
    shared_interests: Mapped[list | None] = mapped_column(JSON, nullable=True)
    friction: Mapped[list | None] = mapped_column(JSON, nullable=True)
    would_meet_again: Mapped[bool] = mapped_column(Boolean, default=False)
    one_line_for_person: Mapped[str | None] = mapped_column(Text, nullable=True)


class RefereeScore(Base):
    __tablename__ = "referee_scores"

    date_id: Mapped[int] = mapped_column(
        ForeignKey("dates.id", ondelete="CASCADE"), primary_key=True
    )
    chemistry: Mapped[float] = mapped_column(Float, nullable=False)
    values_fit: Mapped[float] = mapped_column(Float, nullable=False)
    lifestyle_fit: Mapped[float] = mapped_column(Float, nullable=False)
    ambition_fit: Mapped[float] = mapped_column(Float, nullable=False)
    interests_fit: Mapped[float] = mapped_column(Float, nullable=False)
    tagged_turns: Mapped[list | None] = mapped_column(JSON, nullable=True)


class PairScore(Base):
    __tablename__ = "pair_scores"
    __table_args__ = (UniqueConstraint("run_id", "person_a", "person_b", name="uq_pair_score"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    person_a: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    person_b: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    date_id: Mapped[int | None] = mapped_column(
        ForeignKey("dates.id", ondelete="SET NULL"), nullable=True
    )
    round_used: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    mutual: Mapped[float] = mapped_column(Float, nullable=False)
    referee: Mapped[float] = mapped_column(Float, nullable=False)
    embedding: Mapped[float] = mapped_column(Float, nullable=False)
    final: Mapped[float] = mapped_column(Float, nullable=False)
    why: Mapped[str | None] = mapped_column(Text, nullable=True)
