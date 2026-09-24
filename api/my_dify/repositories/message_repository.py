"""Persistence operations for conversation messages."""

from ..extensions.database import db
from ..models.message import MessageModel


class MessageRepository:
    def create(self, message: MessageModel) -> MessageModel:
        db.session.add(message)
        db.session.commit()
        db.session.refresh(message)
        return message

    def list_by_conversation_id(self, conversation_id: str) -> list[MessageModel]:
        statement = (
            db.select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at.asc())
        )
        return list(db.session.execute(statement).scalars())

    def list_completed_by_conversation_id(
        self,
        conversation_id: str,
    ) -> list[MessageModel]:
        statement = (
            db.select(MessageModel)
            .where(
                MessageModel.conversation_id == conversation_id,
                MessageModel.status == "completed",
            )
            .order_by(MessageModel.created_at.asc())
        )
        return list(db.session.execute(statement).scalars())
