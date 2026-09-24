"""Health-check endpoint."""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    """Report whether the API process is running."""
    return jsonify(status="ok", service="my-dify-api")
