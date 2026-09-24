"""Database model for a conversation belonging to an AI application."""

from datetime import datetime, timezone
from uuid import uuid4

from ..extensions.database import db


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ConversationModel(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    app_id = db.Column(
        db.String(36),
        db.ForeignKey("apps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(100), default="New conversation", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    app = db.relationship("AppModel", back_populates="conversations")
    messages = db.relationship(
        "MessageModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="MessageModel.created_at",
    )
