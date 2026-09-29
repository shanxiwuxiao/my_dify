from flask import Blueprint, jsonify, request, session
from pydantic import ValidationError

from ..extensions.database import db
from ..models.user import UserModel
from ..schemas.auth import Credentials, UserResponse

auth_bp = Blueprint("auth", __name__)


def _serialize(user: UserModel):
    return UserResponse.model_validate(user).model_dump(mode="json")


@auth_bp.post("/api/auth/register")
def register():
    try:
        data = Credentials.model_validate(request.get_json())
    except (ValidationError, TypeError):
        return jsonify(code="invalid_request", message="Invalid email or password"), 400
    existing = db.session.execute(
        db.select(UserModel).where(UserModel.email == data.email)
    ).scalar_one_or_none()
    if existing:
        return jsonify(code="email_exists", message="Email already registered"), 409
    user = UserModel(email=data.email)
    user.set_password(data.password)
    db.session.add(user)
    db.session.commit()
    session.clear()
    session["user_id"] = user.id
    return jsonify(_serialize(user)), 201


@auth_bp.post("/api/auth/login")
def login():
    try:
        data = Credentials.model_validate(request.get_json())
    except (ValidationError, TypeError):
        return jsonify(code="invalid_request", message="Invalid email or password"), 400
    user = db.session.execute(
        db.select(UserModel).where(UserModel.email == data.email)
    ).scalar_one_or_none()
    if user is None or not user.check_password(data.password):
        return jsonify(code="invalid_credentials", message="Invalid email or password"), 401
    session.clear()
    session["user_id"] = user.id
    return jsonify(_serialize(user))


@auth_bp.post("/api/auth/logout")
def logout():
    session.clear()
    return "", 204


@auth_bp.get("/api/auth/me")
def me():
    user_id = session.get("user_id")
    user = db.session.get(UserModel, user_id) if user_id else None
    if user is None:
        return jsonify(code="unauthorized", message="Authentication required"), 401
    return jsonify(_serialize(user))
