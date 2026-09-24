"""Orchestration for persisted, multi-turn conversations."""

from collections.abc import Iterator
from dataclasses import dataclass

from ..core.model_runtime.base import ModelMessage
from ..core.model_runtime.exceptions import ModelRequestError
from ..models.message import MessageModel
from ..repositories.message_repository import MessageRepository
from .chat_service import ChatService
from .conversation_service import ConversationService


@dataclass
class PreparedConversationChat:
    conversation_id: str
    messages: list[ModelMessage]
    model_name: str
    temperature: float
    assistant_message_id: str | None = None


class ConversationChatService:
    def __init__(
        self,
        conversation_service: ConversationService,
        message_repository: MessageRepository,
        chat_service: ChatService,
    ):
        self._conversation_service = conversation_service
        self._message_repository = message_repository
        self._chat_service = chat_service

    def prepare_message(
        self,
        conversation_id: str,
        content: str,
    ) -> PreparedConversationChat:
        conversation = self._conversation_service.get_conversation(conversation_id)
        history = self._message_repository.list_completed_by_conversation_id(
            conversation_id
        )

        messages: list[ModelMessage] = []
        if conversation.app.system_prompt.strip():
            messages.append(
                {
                    "role": "system",
                    "content": conversation.app.system_prompt.strip(),
                }
            )
        messages.extend(
            {"role": message.role, "content": message.content}  # type: ignore[misc]
            for message in history
            if message.role in {"user", "assistant"}
        )
        messages.append({"role": "user", "content": content})

        self._message_repository.create(
            MessageModel(
                conversation_id=conversation_id,
                role="user",
                content=content,
                status="completed",
            )
        )
        self._conversation_service.touch_conversation(conversation)

        return PreparedConversationChat(
            conversation_id=conversation_id,
            messages=messages,
            model_name=conversation.app.model_name,
            temperature=conversation.app.temperature,
        )

    def _save_assistant_message(
        self,
        prepared: PreparedConversationChat,
        content: str,
    ) -> MessageModel:
        message = self._message_repository.create(
            MessageModel(
                conversation_id=prepared.conversation_id,
                role="assistant",
                content=content,
                status="completed",
            )
        )
        conversation = self._conversation_service.get_conversation(
            prepared.conversation_id
        )
        self._conversation_service.touch_conversation(conversation)
        prepared.assistant_message_id = message.id
        return message

    def complete(self, prepared: PreparedConversationChat) -> MessageModel:
        answer = self._chat_service.chat_messages(
            prepared.messages,
            model=prepared.model_name,
            temperature=prepared.temperature,
        )
        if not answer.strip():
            raise ModelRequestError("Model provider returned an empty answer")
        return self._save_assistant_message(prepared, answer)

    def stream(self, prepared: PreparedConversationChat) -> Iterator[str]:
        chunks: list[str] = []
        for delta in self._chat_service.stream_chat_messages(
            prepared.messages,
            model=prepared.model_name,
            temperature=prepared.temperature,
        ):
            chunks.append(delta)
            yield delta

        answer = "".join(chunks)
        if not answer.strip():
            raise ModelRequestError("Model provider returned an empty answer")
        self._save_assistant_message(prepared, answer)

    def list_messages(self, conversation_id: str) -> list[MessageModel]:
        self._conversation_service.get_conversation(conversation_id)
        return self._message_repository.list_by_conversation_id(conversation_id)
