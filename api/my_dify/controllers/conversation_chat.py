"""HTTP endpoints for persisted, multi-turn conversation messages."""

from collections.abc import Iterator
from typing import Any

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from ..core.model_runtime.exceptions import ModelError
from ..schemas.chat import ChatRequest
from ..schemas.message import ConversationChatResponse, MessageResponse
from ..services.conversation_chat_service import ConversationChatService
from ..services.exceptions import ConversationNotFoundError
from .chat import format_sse, invalid_request

conversation_chat_bp = Blueprint("conversation_chat", __name__)


def _conversation_chat_service() -> ConversationChatService:
    return current_app.extensions["conversation_chat_service"]


def _serialize_message(message: Any) -> dict[str, Any]:
    return MessageResponse.model_validate(message).model_dump(mode="json")


def _read_chat_request():
    try:
        payload = request.get_json()
    except (BadRequest, UnsupportedMediaType):
        return None
    if not isinstance(payload, dict):
        return None
    try:
        return ChatRequest.model_validate(payload)
    except ValidationError:
        return None


def _conversation_not_found():
    return jsonify(
        code="conversation_not_found",
        message="Conversation not found",
    ), 404


@conversation_chat_bp.get("/api/conversations/<conversation_id>/messages")
def list_messages(conversation_id: str):
    try:
        messages = _conversation_chat_service().list_messages(conversation_id)
    except ConversationNotFoundError:
        return _conversation_not_found()
    items = [_serialize_message(message) for message in messages]
    return jsonify(items=items, total=len(items))


@conversation_chat_bp.post("/api/conversations/<conversation_id>/messages")
def create_message(conversation_id: str):
    chat_request = _read_chat_request()
    if chat_request is None:
        return invalid_request("Invalid request")

    service = _conversation_chat_service()
    try:
        prepared = service.prepare_message(conversation_id, chat_request.message)
        assistant_message = service.complete(prepared)
    except ConversationNotFoundError:
        return _conversation_not_found()
    except ModelError:
        current_app.logger.exception("Conversation model request failed")
        return jsonify(code="model_error", message="Model request failed"), 502

    response = ConversationChatResponse(
        conversation_id=conversation_id,
        message=MessageResponse.model_validate(assistant_message),
    )
    return jsonify(response.model_dump(mode="json"))


@conversation_chat_bp.post("/api/conversations/<conversation_id>/messages/stream")
def stream_message(conversation_id: str):
    chat_request = _read_chat_request()
    if chat_request is None:
        return invalid_request("Invalid request")

    service = _conversation_chat_service()
    try:
        prepared = service.prepare_message(conversation_id, chat_request.message)
    except ConversationNotFoundError:
        return _conversation_not_found()

    logger = current_app.logger

    def generate_events() -> Iterator[str]:
        try:
            for delta in service.stream(prepared):
                yield format_sse("message", {"delta": delta})
        except ModelError:
            logger.exception("Streaming conversation model request failed")
            yield format_sse(
                "error",
                {"code": "model_error", "message": "Model request failed"},
            )
            return

        yield format_sse(
            "done",
            {
                "conversation_id": prepared.conversation_id,
                "message_id": prepared.assistant_message_id,
            },
        )

    return Response(
        stream_with_context(generate_events()),
        content_type="text/event-stream; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
