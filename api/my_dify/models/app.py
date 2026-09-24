"""Database model for an AI application."""

from datetime import datetime, timezone
from uuid import uuid4

from ..extensions.database import db


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AppModel(db.Model):
    __tablename__ = "apps"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), default="", nullable=False)
    system_prompt = db.Column(db.Text, default="", nullable=False)
    model_name = db.Column(db.String(100), default="deepseek-flash", nullable=False)
    temperature = db.Column(db.Float, default=0.7, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    conversations = db.relationship(
        "ConversationModel",
        back_populates="app",
        cascade="all, delete-orphan",
    )
