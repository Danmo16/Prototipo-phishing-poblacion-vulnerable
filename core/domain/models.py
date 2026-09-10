# core/domain/models.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class User(Base):
    """Represents an API user authenticated via JWT."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="analyst")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.id!r} username={self.username!r} role={self.role!r}>"


class Template(Base):
    """Represents an email/SMS/voice template used in a phishing campaign."""

    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    subject = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    html_body = Column(Text, nullable=False)
    signals = Column(JSON, nullable=True)
    version = Column(Integer, default=1, nullable=False)

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
    uid = Column(String(64), unique=True, nullable=True, index=True)
    meta = Column(JSON, nullable=True)

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

    campaign = relationship("Campaign", back_populates="events")
    target = relationship("Target", back_populates="events")
    template = relationship("Template")

    def __repr__(self) -> str:
        return f"<Event id={self.id!r} type={self.event_type!r} occurred_at={self.occurred_at!r}>"