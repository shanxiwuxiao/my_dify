"""Conversation management use cases."""

from ..models.conversation import ConversationModel
from ..repositories.conversation_repository import ConversationRepository
from .app_service import AppService
from .exceptions import ConversationNotFoundError


class ConversationService:
    def __init__(
        self,
        repository: ConversationRepository,
        app_service: AppService,
    ):
        self._repository = repository
        self._app_service = app_service

    def create_conversation(self, app_id: str, name: str) -> ConversationModel:
        self._app_service.get_app(app_id)
        return self._repository.create(ConversationModel(app_id=app_id, name=name))

    def list_conversations(self, app_id: str) -> list[ConversationModel]:
        self._app_service.get_app(app_id)
        return self._repository.list_by_app_id(app_id)

    def get_conversation(self, conversation_id: str) -> ConversationModel:
        conversation = self._repository.get_by_id(
            conversation_id,
            self._app_service._owner_id(),
        )
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        return conversation

    def touch_conversation(self, conversation: ConversationModel) -> ConversationModel:
        return self._repository.touch(conversation)

    def rename_conversation(
        self,
        conversation_id: str,
        name: str,
    ) -> ConversationModel:
        conversation = self.get_conversation(conversation_id)
        return self._repository.update_name(conversation, name)

    def delete_conversation(self, conversation_id: str) -> None:
        conversation = self.get_conversation(conversation_id)
        self._repository.delete(conversation)
