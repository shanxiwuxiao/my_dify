from flask.testing import FlaskClient

from conftest import FakeModelClient


def create_application(client: FlaskClient) -> dict:
    response = client.post(
        "/api/apps",
        json={
            "name": "Python 老师",
            "system_prompt": "你是一名严格的 Python 老师",
            "model_name": "application-model",
            "temperature": 0.2,
        },
    )
    assert response.status_code == 201
    return response.get_json()


def test_application_chat_uses_saved_configuration(
    client: FlaskClient,
    model_client: FakeModelClient,
) -> None:
    application = create_application(client)

    response = client.post(
        f"/api/apps/{application['id']}/chat",
        json={"message": "什么是装饰器？"},
    )

    assert response.status_code == 200
    assert response.get_json() == {"answer": "Fake answer: 什么是装饰器？"}
    assert model_client.messages == [
        {"role": "system", "content": "你是一名严格的 Python 老师"},
        {"role": "user", "content": "什么是装饰器？"},
    ]
    assert model_client.model == "application-model"
    assert model_client.temperature == 0.2


def test_application_stream_chat_uses_saved_configuration(
    client: FlaskClient,
    model_client: FakeModelClient,
) -> None:
    application = create_application(client)

    response = client.post(
        f"/api/apps/{application['id']}/chat/stream",
        json={"message": "解释生成器"},
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.content_type == "text/event-stream; charset=utf-8"
    assert 'event: message\ndata: {"delta":"解释生成器"}\n\n' in body
    assert body.count("event: done\n") == 1
    assert model_client.messages == [
        {"role": "system", "content": "你是一名严格的 Python 老师"},
        {"role": "user", "content": "解释生成器"},
    ]
    assert model_client.model == "application-model"
    assert model_client.temperature == 0.2


def test_application_chat_returns_404_for_missing_app(client: FlaskClient) -> None:
    response = client.post(
        "/api/apps/missing/chat",
        json={"message": "你好"},
    )

    assert response.status_code == 404
    assert response.get_json()["code"] == "app_not_found"


def test_application_stream_chat_returns_json_404_before_streaming(
    client: FlaskClient,
) -> None:
    response = client.post(
        "/api/apps/missing/chat/stream",
        json={"message": "你好"},
    )

    assert response.status_code == 404
    assert response.is_json
    assert response.get_json()["code"] == "app_not_found"


def test_application_chat_rejects_invalid_request(client: FlaskClient) -> None:
    application = create_application(client)

    response = client.post(f"/api/apps/{application['id']}/chat", json={})

    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_request"


def test_application_stream_chat_rejects_invalid_request(
    client: FlaskClient,
) -> None:
    application = create_application(client)

    response = client.post(f"/api/apps/{application['id']}/chat/stream", json={})

    assert response.status_code == 400
    assert response.is_json
