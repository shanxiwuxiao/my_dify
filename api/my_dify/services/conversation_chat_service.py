"""Orchestration for persisted, multi-turn conversations."""

from collections.abc import Iterator
from dataclasses import dataclass

from ..core.model_runtime.base import ModelMessage
from ..core.model_runtime.exceptions import ModelRequestError
from ..models.message import MessageModel
from ..repositories.message_repository import MessageRepository
from .chat_service import ChatService
from .conversation_service import ConversationService
from .model_runtime_service import ModelRuntimeService
from .knowledge_service import KnowledgeService


@dataclass
class PreparedConversationChat:
    conversation_id: str
    messages: list[ModelMessage]
    model_name: str
    temperature: float
    assistant_message_id: str | None = None
    chat_service: ChatService | None = None
    sources: list[dict] | None = None


class ConversationChatService:
    def __init__(
        self,
        conversation_service: ConversationService,
        message_repository: MessageRepository,
        model_runtime_service: ModelRuntimeService,
        knowledge_service: KnowledgeService,
    ):
        self._conversation_service = conversation_service
        self._message_repository = message_repository
        self._model_runtime = model_runtime_service
        self._knowledge = knowledge_service

    def prepare_message(
        self,
        conversation_id: str,
        content: str,
    ) -> PreparedConversationChat:
        conversation = self._conversation_service.get_conversation(conversation_id)
        history = self._message_repository.list_completed_by_conversation_id(
            conversation_id
        )

        runtime = self._conversation_service._app_service.runtime_config(conversation.app_id)
        sources = self._knowledge.retrieve_for_app(conversation.app, content)
        messages: list[ModelMessage] = []
        system_content = runtime.system_prompt.strip()
        if sources:
            context = "\n\n".join(f"[{item['document_name']}]\n{item['content']}" for item in sources)
            system_content += f"\n\n请优先依据以下知识库资料回答；资料不足时明确说明。\n{context}"
        if system_content:
            messages.append(
                {
                    "role": "system",
                    "content": system_content,
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
            model_name=runtime.model_name,
            temperature=runtime.temperature,
            chat_service=self._model_runtime.for_config(runtime),
            sources=sources,
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
        assert prepared.chat_service is not None
        answer = prepared.chat_service.chat_messages(
            prepared.messages,
            model=prepared.model_name,
            temperature=prepared.temperature,
        )
        if not answer.strip():
            raise ModelRequestError("Model provider returned an empty answer")
        return self._save_assistant_message(prepared, answer)

    def stream(self, prepared: PreparedConversationChat) -> Iterator[str]:
        chunks: list[str] = []
        assert prepared.chat_service is not None
        for delta in prepared.chat_service.stream_chat_messages(
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
