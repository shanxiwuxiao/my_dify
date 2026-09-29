from collections.abc import Iterator

from my_dify import create_app
from my_dify.core.model_runtime.base import ModelMessage
from my_dify.core.model_runtime.exceptions import ModelRequestError
from my_dify.services.chat_service import ChatService
from my_dify.configs.settings import Settings
from my_dify.extensions.database import db


class FailingModelClient:
    def generate(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        raise ModelRequestError("sensitive provider detail")

    def generate_stream(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> Iterator[str]:
        raise ModelRequestError("sensitive streaming provider detail")
        yield


def test_chat_hides_model_error_details() -> None:
    app = create_app(settings=Settings(database_url="sqlite:///:memory:", _env_file=None), chat_service=ChatService(FailingModelClient()))
    app.config.update(TESTING=True)
    with app.app_context():
        db.create_all()

    with app.test_client() as client:
        client.post("/api/auth/register", json={"email": "error@example.com", "password": "password123"})
        response = client.post("/api/chat", json={"message": "你好"})

    assert response.status_code == 502
    assert response.get_json() == {
        "code": "model_error",
        "message": "Model request failed",
    }


def test_stream_chat_hides_model_error_details() -> None:
    app = create_app(settings=Settings(database_url="sqlite:///:memory:", _env_file=None), chat_service=ChatService(FailingModelClient()))
    app.config.update(TESTING=True)
    with app.app_context():
        db.create_all()

    with app.test_client() as client:
        client.post("/api/auth/register", json={"email": "stream@example.com", "password": "password123"})
        response = client.post("/api/chat/stream", json={"message": "你好"})
        body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "event: error\n" in body
    assert 'data: {"code":"model_error","message":"Model request failed"}\n\n' in body
    assert "sensitive streaming provider detail" not in body
    assert "event: done\n" not in body
