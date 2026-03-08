"""SQLAlchemy ORM models for the phishing prototype.

These classes map the conceptual entities of the system—campaigns,
templates, segments, targets and events—to relational database tables.
Using SQLAlchemy's declarative ORM allows us to keep the Python
representations and the database schema in sync while still writing
idiomatic Python code. Relationships between entities are declared via
foreign keys and SQLAlchemy's relationship function.

Note: you can switch primary key types (e.g., to UUIDs) if needed, but
integers suffice for the initial prototype. Default values and
timestamps are defined at the model level.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Template(Base):
    """Represents an email/SMS/voice template used in a phishing campaign."""

    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    html_body = Column(String, nullable=False)
    signals = Column(JSON, nullable=True)
    version = Column(Integer, default=1, nullable=False)

    # Relationship backref to campaigns
    campaigns = relationship("Campaign", back_populates="template", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Template id={self.id!r} name={self.name!r} channel={self.channel!r}>"


class Segment(Base):
    """Group of targets sharing demographic attributes."""

    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    age_bracket = Column(String(50))
    gender = Column(String(50))
    education = Column(String(50))

    # Relationship to targets and campaigns
    targets = relationship("Target", back_populates="segment", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="segment", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Segment id={self.id!r} age={self.age_bracket!r} gender={self.gender!r} education={self.education!r}>"


class Target(Base):
    """Represents an individual recipient in a campaign."""

    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)
    recipient = Column(String(255), nullable=False)
    meta = Column(JSON, nullable=True)
    uid = Column(String(64), unique=True, nullable=True, index=True)

    # Relationship back to segment and events
    segment = relationship("Segment", back_populates="targets")
    events = relationship("Event", back_populates="target", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Target id={self.id!r} recipient={self.recipient!r}>"


class Campaign(Base):
    """Represents a phishing campaign configured for a specific segment and template."""

    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel = Column(String(50), nullable=False)
    launched_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="draft")
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)

    # Relationships to template, segment, and events
    template = relationship("Template", back_populates="campaigns")
    segment = relationship("Segment", back_populates="campaigns")
    events = relationship("Event", back_populates="campaign", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Campaign id={self.id!r} channel={self.channel!r} status={self.status!r}>"


class Event(Base):
    """Event captured when a recipient opens, clicks, reports, etc., a phishing message."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    meta = Column(JSON, nullable=True)

    # Relationships back to campaign, target, and template
    campaign = relationship("Campaign", back_populates="events")
    target = relationship("Target", back_populates="events")
    template = relationship("Template")

    def __repr__(self) -> str:
        return f"<Event id={self.id!r} type={self.event_type!r} occurred_at={self.occurred_at!r}>"