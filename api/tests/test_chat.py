from flask.testing import FlaskClient


def test_chat_returns_answer(client: FlaskClient) -> None:
    response = client.post("/api/chat", json={"message": "你好"})

    assert response.status_code == 200
    assert response.get_json() == {"answer": "Fake answer: 你好"}


def test_chat_strips_surrounding_whitespace(client: FlaskClient) -> None:
    response = client.post("/api/chat", json={"message": "  你好  "})

    assert response.status_code == 200
    assert response.get_json() == {"answer": "Fake answer: 你好"}


def test_chat_rejects_missing_message(client: FlaskClient) -> None:
    response = client.post("/api/chat", json={})

    assert response.status_code == 400
    assert response.get_json() == {
        "code": "invalid_request",
        "message": "message is required",
    }


def test_chat_rejects_empty_message(client: FlaskClient) -> None:
    response = client.post("/api/chat", json={"message": ""})

    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_request"


def test_chat_rejects_whitespace_only_message(client: FlaskClient) -> None:
    response = client.post("/api/chat", json={"message": "   "})

    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_request"


def test_chat_rejects_non_json_request(client: FlaskClient) -> None:
    response = client.post("/api/chat", data="hello", content_type="text/plain")

    assert response.status_code == 400
    assert response.get_json() == {
        "code": "invalid_request",
        "message": "request body must be valid JSON",
    }


def test_chat_rejects_message_longer_than_limit(client: FlaskClient) -> None:
    response = client.post("/api/chat", json={"message": "a" * 2001})

    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_request"


def test_stream_chat_returns_sse_events(client: FlaskClient) -> None:
    response = client.post("/api/chat/stream", json={"message": "你好"})
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.content_type == "text/event-stream; charset=utf-8"
    assert response.headers["Cache-Control"] == "no-cache"
    assert response.headers["X-Accel-Buffering"] == "no"
    assert 'event: message\ndata: {"delta":"Fake "}\n\n' in body
    assert 'event: message\ndata: {"delta":"answer: "}\n\n' in body
    assert 'event: message\ndata: {"delta":"你好"}\n\n' in body
    assert body.count("event: done\n") == 1


def test_stream_chat_rejects_invalid_request_before_streaming(
    client: FlaskClient,
) -> None:
    response = client.post("/api/chat/stream", json={})

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["code"] == "invalid_request"
