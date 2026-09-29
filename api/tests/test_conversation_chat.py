from collections.abc import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from conftest import FakeModelClient
from my_dify import create_app
from my_dify.configs.settings import Settings
from my_dify.core.model_runtime.base import ModelMessage
from my_dify.core.model_runtime.exceptions import ModelRequestError
from my_dify.extensions.database import db
from my_dify.services.chat_service import ChatService


def create_application(client: FlaskClient) -> dict:
    response = client.post(
        "/api/apps",
        json={
            "name": "Python 老师",
            "system_prompt": "你是一名 Python 老师",
            "model_name": "conversation-model",
            "temperature": 0.2,
        },
    )
    assert response.status_code == 201
    return response.get_json()


def create_conversation(client: FlaskClient) -> dict:
    application = create_application(client)
    response = client.post(
        f"/api/apps/{application['id']}/conversations",
        json={"name": "学习会话"},
    )
    assert response.status_code == 201
    return response.get_json()


def test_conversation_chat_saves_user_and_assistant_messages(
    client: FlaskClient,
) -> None:
    conversation = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        json={"message": "你好"},
    )
    messages = client.get(
        f"/api/conversations/{conversation['id']}/messages"
    ).get_json()["items"]

    assert response.status_code == 200
    assert response.get_json()["conversation_id"] == conversation["id"]
    assert response.get_json()["message"]["content"] == "Fake answer: 你好"
    assert [(item["role"], item["content"]) for item in messages] == [
        ("user", "你好"),
        ("assistant", "Fake answer: 你好"),
    ]


def test_second_turn_contains_first_turn_history(
    client: FlaskClient,
    model_client: FakeModelClient,
) -> None:
    conversation = create_conversation(client)
    url = f"/api/conversations/{conversation['id']}/messages"
    client.post(url, json={"message": "我叫小明"})

    client.post(url, json={"message": "我叫什么？"})

    assert model_client.messages == [
        {"role": "system", "content": "你是一名 Python 老师"},
        {"role": "user", "content": "我叫小明"},
        {"role": "assistant", "content": "Fake answer: 我叫小明"},
        {"role": "user", "content": "我叫什么？"},
    ]
    assert model_client.model == "conversation-model"
    assert model_client.temperature == 0.2


def test_messages_are_isolated_between_conversations(client: FlaskClient) -> None:
    first = create_conversation(client)
    second = create_conversation(client)
    client.post(
        f"/api/conversations/{first['id']}/messages",
        json={"message": "第一组"},
    )
    client.post(
        f"/api/conversations/{second['id']}/messages",
        json={"message": "第二组"},
    )

    first_messages = client.get(
        f"/api/conversations/{first['id']}/messages"
    ).get_json()["items"]

    assert all("第二组" not in item["content"] for item in first_messages)
    assert len(first_messages) == 2


def test_stream_chat_saves_complete_assistant_message(
    client: FlaskClient,
) -> None:
    conversation = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation['id']}/messages/stream",
        json={"message": "解释生成器"},
    )
    body = response.get_data(as_text=True)
    messages = client.get(
        f"/api/conversations/{conversation['id']}/messages"
    ).get_json()["items"]

    assert response.status_code == 200
    assert response.content_type == "text/event-stream; charset=utf-8"
    assert body.count("event: done\n") == 1
    assert '"message_id":' in body
    assert messages[-1]["role"] == "assistant"
    assert messages[-1]["content"] == "Fake answer: 解释生成器"


def test_second_stream_turn_contains_first_stream_history(
    client: FlaskClient,
    model_client: FakeModelClient,
) -> None:
    conversation = create_conversation(client)
    url = f"/api/conversations/{conversation['id']}/messages/stream"
    client.post(url, json={"message": "第一轮"}).get_data()

    client.post(url, json={"message": "第二轮"}).get_data()

    assert model_client.messages == [
        {"role": "system", "content": "你是一名 Python 老师"},
        {"role": "user", "content": "第一轮"},
        {"role": "assistant", "content": "Fake answer: 第一轮"},
        {"role": "user", "content": "第二轮"},
    ]


def test_missing_conversation_returns_json_404_before_streaming(
    client: FlaskClient,
) -> None:
    response = client.post(
        "/api/conversations/missing/messages/stream",
        json={"message": "你好"},
    )

    assert response.status_code == 404
    assert response.is_json
    assert response.get_json()["code"] == "conversation_not_found"


def test_missing_conversation_messages_returns_404(client: FlaskClient) -> None:
    response = client.get("/api/conversations/missing/messages")

    assert response.status_code == 404


class FailingModelClient:
    def generate(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        raise ModelRequestError("sensitive provider error")

    def generate_stream(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> Iterator[str]:
        raise ModelRequestError("sensitive streaming error")
        yield


@pytest.fixture()
def failing_app() -> Iterator[Flask]:
    settings = Settings(database_url="sqlite:///:memory:", _env_file=None)
    app = create_app(
        settings=settings,
        chat_service=ChatService(FailingModelClient()),
    )
    app.config.update(TESTING=True)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_model_error_keeps_user_message_without_assistant(
    failing_app: Flask,
) -> None:
    client = failing_app.test_client()
    client.post("/api/auth/register", json={"email": "failure@example.com", "password": "password123"})
    conversation = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        json={"message": "失败消息"},
    )
    messages = client.get(
        f"/api/conversations/{conversation['id']}/messages"
    ).get_json()["items"]

    assert response.status_code == 502
    assert response.get_json()["code"] == "model_error"
    assert [(item["role"], item["content"]) for item in messages] == [
        ("user", "失败消息")
    ]


def test_stream_model_error_emits_error_without_done(
    failing_app: Flask,
) -> None:
    client = failing_app.test_client()
    client.post("/api/auth/register", json={"email": "stream-failure@example.com", "password": "password123"})
    conversation = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation['id']}/messages/stream",
        json={"message": "失败消息"},
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "event: error\n" in body
    assert "event: done\n" not in body
    assert "sensitive streaming error" not in body
