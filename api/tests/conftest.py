import pytest
from collections.abc import Iterator
from flask import Flask
from flask.testing import FlaskClient

from my_dify import create_app
from my_dify.configs.settings import Settings
from my_dify.core.model_runtime.base import ModelMessage
from my_dify.extensions.database import db
from my_dify.services.chat_service import ChatService


class FakeModelClient:
    def __init__(self):
        self.messages: list[ModelMessage] | None = None
        self.model: str | None = None
        self.temperature: float | None = None

    def _record(
        self,
        messages: list[ModelMessage],
        model: str | None,
        temperature: float | None,
    ) -> None:
        self.messages = messages
        self.model = model
        self.temperature = temperature

    def generate(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        self._record(messages, model, temperature)
        return f"Fake answer: {messages[-1]['content']}"

    def generate_stream(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> Iterator[str]:
        self._record(messages, model, temperature)
        yield "Fake "
        yield "answer: "
        yield messages[-1]["content"]


@pytest.fixture()
def model_client() -> FakeModelClient:
    return FakeModelClient()


@pytest.fixture()
def app(model_client: FakeModelClient) -> Flask:
    chat_service = ChatService(model_client)
    settings = Settings(database_url="sqlite:///:memory:", _env_file=None)
    app = create_app(settings=settings, chat_service=chat_service)
    app.config.update(TESTING=True)

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    client = app.test_client()
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    return client
