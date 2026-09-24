"""Chat HTTP endpoints."""

import json
from collections.abc import Iterator
from typing import Any

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from ..core.model_runtime.exceptions import ModelError
from ..schemas.chat import ChatRequest, ChatResponse
from ..services.chat_service import ChatService

chat_bp = Blueprint("chat", __name__)


def invalid_request(message: str = "message is required") -> tuple[Any, int]:
    """Build the public error response for invalid chat payloads."""
    return jsonify(code="invalid_request", message=message), 400


def format_sse(event: str, data: dict[str, Any]) -> str:
    """Serialize one Server-Sent Event frame."""
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {encoded}\n\n"


@chat_bp.post("/api/chat")
def chat():
    """Validate a chat request and return a model-generated answer."""
    try:
        payload = request.get_json()
    except (BadRequest, UnsupportedMediaType):
        return invalid_request("request body must be valid JSON")

    if not isinstance(payload, dict):
        return invalid_request("request body must be a JSON object")

    try:
        chat_request = ChatRequest.model_validate(payload)
    except ValidationError:
        return invalid_request()

    chat_service: ChatService = current_app.extensions["chat_service"]
    try:
        answer = chat_service.chat(chat_request.message)
    except ModelError:
        current_app.logger.exception("Model request failed")
        return jsonify(code="model_error", message="Model request failed"), 502

    response = ChatResponse(answer=answer)
    return jsonify(response.model_dump())


@chat_bp.post("/api/chat/stream")
def stream_chat():
    """Validate a chat request and stream model-generated answer deltas."""
    try:
        payload = request.get_json()
    except (BadRequest, UnsupportedMediaType):
        return invalid_request("request body must be valid JSON")

    if not isinstance(payload, dict):
        return invalid_request("request body must be a JSON object")

    try:
        chat_request = ChatRequest.model_validate(payload)
    except ValidationError:
        return invalid_request()

    chat_service: ChatService = current_app.extensions["chat_service"]
    logger = current_app.logger

    def generate_events() -> Iterator[str]:
        try:
            for delta in chat_service.stream_chat(chat_request.message):
                yield format_sse("message", {"delta": delta})
        except ModelError:
            logger.exception("Streaming model request failed")
            yield format_sse(
                "error",
                {"code": "model_error", "message": "Model request failed"},
            )
            return

        yield format_sse("done", {})

    return Response(
        stream_with_context(generate_events()),
        content_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
