"""HTTP endpoints for managing conversations."""

from typing import Any

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from ..schemas.conversation import ConversationCreate, ConversationResponse
from ..services.conversation_service import ConversationService
from ..services.exceptions import AppNotFoundError, ConversationNotFoundError

conversations_bp = Blueprint("conversations", __name__)


def _serialize_conversation(conversation: Any) -> dict[str, Any]:
    return ConversationResponse.model_validate(conversation).model_dump(mode="json")


def _conversation_service() -> ConversationService:
    return current_app.extensions["conversation_service"]


def _app_not_found():
    return jsonify(code="app_not_found", message="Application not found"), 404


def _conversation_not_found():
    return jsonify(
        code="conversation_not_found",
        message="Conversation not found",
    ), 404


@conversations_bp.post("/api/apps/<app_id>/conversations")
def create_conversation(app_id: str):
    try:
        payload = request.get_json(silent=True)
    except (BadRequest, UnsupportedMediaType):
        payload = None
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        return jsonify(code="invalid_request", message="Invalid request"), 400
    try:
        data = ConversationCreate.model_validate(payload)
        conversation = _conversation_service().create_conversation(app_id, data.name)
    except ValidationError:
        return jsonify(code="invalid_request", message="Invalid request"), 400
    except AppNotFoundError:
        return _app_not_found()
    return jsonify(_serialize_conversation(conversation)), 201


@conversations_bp.get("/api/apps/<app_id>/conversations")
def list_conversations(app_id: str):
    try:
        conversations = _conversation_service().list_conversations(app_id)
    except AppNotFoundError:
        return _app_not_found()
    items = [_serialize_conversation(item) for item in conversations]
    return jsonify(items=items, total=len(items))


@conversations_bp.get("/api/conversations/<conversation_id>")
def get_conversation(conversation_id: str):
    try:
        conversation = _conversation_service().get_conversation(conversation_id)
    except ConversationNotFoundError:
        return _conversation_not_found()
    return jsonify(_serialize_conversation(conversation))


@conversations_bp.delete("/api/conversations/<conversation_id>")
def delete_conversation(conversation_id: str):
    try:
        _conversation_service().delete_conversation(conversation_id)
    except ConversationNotFoundError:
        return _conversation_not_found()
    return "", 204
