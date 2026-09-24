"""Chat endpoints whose behavior is configured by a saved application."""

from collections.abc import Iterator

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from ..core.model_runtime.exceptions import ModelError
from ..schemas.chat import ChatRequest, ChatResponse
from ..services.app_service import AppService
from ..services.chat_service import ChatService
from ..services.exceptions import AppNotFoundError
from .chat import format_sse, invalid_request

app_chat_bp = Blueprint("app_chat", __name__)


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


def _app_not_found():
    return jsonify(code="app_not_found", message="Application not found"), 404


@app_chat_bp.post("/api/apps/<app_id>/chat")
def chat_with_application(app_id: str):
    chat_request = _read_chat_request()
    if chat_request is None:
        return invalid_request("Invalid request")

    app_service: AppService = current_app.extensions["app_service"]
    chat_service: ChatService = current_app.extensions["chat_service"]
    try:
        app = app_service.get_app(app_id)
        answer = chat_service.chat(
            chat_request.message,
            system_prompt=app.system_prompt,
            model_name=app.model_name,
            temperature=app.temperature,
        )
    except AppNotFoundError:
        return _app_not_found()
    except ModelError:
        current_app.logger.exception("Application model request failed")
        return jsonify(code="model_error", message="Model request failed"), 502

    return jsonify(ChatResponse(answer=answer).model_dump())


@app_chat_bp.post("/api/apps/<app_id>/chat/stream")
def stream_chat_with_application(app_id: str):
    chat_request = _read_chat_request()
    if chat_request is None:
        return invalid_request("Invalid request")

    app_service: AppService = current_app.extensions["app_service"]
    chat_service: ChatService = current_app.extensions["chat_service"]
    try:
        app = app_service.get_app(app_id)
    except AppNotFoundError:
        return _app_not_found()

    logger = current_app.logger

    def generate_events() -> Iterator[str]:
        try:
            for delta in chat_service.stream_chat(
                chat_request.message,
                system_prompt=app.system_prompt,
                model_name=app.model_name,
                temperature=app.temperature,
            ):
                yield format_sse("message", {"delta": delta})
        except ModelError:
            logger.exception("Streaming application model request failed")
            yield format_sse(
                "error",
                {"code": "model_error", "message": "Model request failed"},
            )
            return
        yield format_sse("done", {})

    return Response(
        stream_with_context(generate_events()),
        content_type="text/event-stream; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
