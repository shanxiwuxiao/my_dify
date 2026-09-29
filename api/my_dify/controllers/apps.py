"""HTTP endpoints for managing AI applications."""

from typing import Any

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from ..schemas.app import AppCreate, AppResponse, AppUpdate
from ..schemas.app_version import AppVersionResponse
from ..services.app_service import AppService
from ..services.exceptions import AppNotFoundError
from ..services.model_provider_service import ProviderNotFoundError

apps_bp = Blueprint("apps", __name__)


def _app_service() -> AppService:
    return current_app.extensions["app_service"]


def _serialize_app(app: Any) -> dict[str, Any]:
    return AppResponse.model_validate(app).model_dump(mode="json")


def _read_json_object() -> dict[str, Any] | None:
    try:
        payload = request.get_json()
    except (BadRequest, UnsupportedMediaType):
        return None
    return payload if isinstance(payload, dict) else None


def _invalid_request():
    return jsonify(code="invalid_request", message="Invalid request"), 400


def _app_not_found():
    return jsonify(code="app_not_found", message="Application not found"), 404


@apps_bp.post("/api/apps")
def create_application():
    payload = _read_json_object()
    if payload is None:
        return _invalid_request()
    try:
        data = AppCreate.model_validate(payload)
    except ValidationError:
        return _invalid_request()

    try:
        app = _app_service().create_app(data)
    except ProviderNotFoundError:
        return jsonify(code="provider_not_found", message="Model provider not found"), 404
    return jsonify(_serialize_app(app)), 201


@apps_bp.get("/api/apps")
def list_applications():
    apps = _app_service().list_apps()
    items = [_serialize_app(app) for app in apps]
    return jsonify(items=items, total=len(items))


@apps_bp.get("/api/apps/<app_id>")
def get_application(app_id: str):
    try:
        app = _app_service().get_app(app_id)
    except AppNotFoundError:
        return _app_not_found()
    return jsonify(_serialize_app(app))


@apps_bp.patch("/api/apps/<app_id>")
def update_application(app_id: str):
    payload = _read_json_object()
    if payload is None:
        return _invalid_request()
    try:
        data = AppUpdate.model_validate(payload)
        app = _app_service().update_app(app_id, data)
    except ValidationError:
        return _invalid_request()
    except AppNotFoundError:
        return _app_not_found()
    except ProviderNotFoundError:
        return jsonify(code="provider_not_found", message="Model provider not found"), 404
    return jsonify(_serialize_app(app))


@apps_bp.delete("/api/apps/<app_id>")
def delete_application(app_id: str):
    try:
        _app_service().delete_app(app_id)
    except AppNotFoundError:
        return _app_not_found()
    return "", 204


@apps_bp.post("/api/apps/<app_id>/publish")
def publish_application(app_id: str):
    try:
        version = _app_service().publish(app_id)
    except AppNotFoundError:
        return _app_not_found()
    return jsonify(AppVersionResponse.model_validate(version).model_dump(mode="json")), 201


@apps_bp.get("/api/apps/<app_id>/versions")
def list_application_versions(app_id: str):
    try:
        versions = _app_service().list_versions(app_id)
    except AppNotFoundError:
        return _app_not_found()
    items = [AppVersionResponse.model_validate(item).model_dump(mode="json") for item in versions]
    return jsonify(items=items, total=len(items))
