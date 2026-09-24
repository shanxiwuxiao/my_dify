"""Persistence operations for conversations."""

from datetime import datetime, timezone

from ..extensions.database import db
from ..models.conversation import ConversationModel


class ConversationRepository:
    def create(self, conversation: ConversationModel) -> ConversationModel:
        db.session.add(conversation)
        db.session.commit()
        db.session.refresh(conversation)
        return conversation

    def list_by_app_id(self, app_id: str) -> list[ConversationModel]:
        statement = (
            db.select(ConversationModel)
            .where(ConversationModel.app_id == app_id)
            .order_by(ConversationModel.updated_at.desc())
        )
        return list(db.session.execute(statement).scalars())

    def get_by_id(self, conversation_id: str) -> ConversationModel | None:
        return db.session.get(ConversationModel, conversation_id)

    def touch(self, conversation: ConversationModel) -> ConversationModel:
        conversation.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        db.session.refresh(conversation)
        return conversation

    def delete(self, conversation: ConversationModel) -> None:
        db.session.delete(conversation)
        db.session.commit()
