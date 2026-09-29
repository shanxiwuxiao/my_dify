from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError
from ..schemas.model_provider import ModelProviderCreate, ModelProviderResponse
from ..services.model_provider_service import ModelProviderService, ProviderNotFoundError

model_providers_bp = Blueprint("model_providers", __name__)


def _service() -> ModelProviderService: return current_app.extensions["model_provider_service"]


def _serialize(provider):
    return ModelProviderResponse(
        id=provider.id, name=provider.name, base_url=provider.base_url,
        default_model=provider.default_model, api_key_masked="••••••••",
        created_at=provider.created_at,
    ).model_dump(mode="json")


@model_providers_bp.post("/api/model-providers")
def create_provider():
    try: data = ModelProviderCreate.model_validate(request.get_json())
    except (ValidationError, TypeError): return jsonify(code="invalid_request", message="Invalid request"), 400
    return jsonify(_serialize(_service().create(data))), 201


@model_providers_bp.get("/api/model-providers")
def list_providers():
    items = [_serialize(item) for item in _service().list()]
    return jsonify(items=items, total=len(items))


@model_providers_bp.delete("/api/model-providers/<provider_id>")
def delete_provider(provider_id: str):
    try: _service().delete(provider_id)
    except ProviderNotFoundError: return jsonify(code="provider_not_found", message="Model provider not found"), 404
    return "", 204
