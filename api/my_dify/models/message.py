"""Database model for a user or assistant conversation message."""

from datetime import datetime, timezone
from uuid import uuid4

from ..extensions.database import db


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MessageModel(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    conversation_id = db.Column(
        db.String(36),
        db.ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="completed", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    conversation = db.relationship("ConversationModel", back_populates="messages")
