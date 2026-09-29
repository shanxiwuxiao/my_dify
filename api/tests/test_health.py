from flask.testing import FlaskClient


def test_health(client: FlaskClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "service": "my-dify-api",
        "status": "ok",
    }


def test_security_headers_are_added(client: FlaskClient) -> None:
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_oversized_request_returns_json(app) -> None:
    app.config["MAX_CONTENT_LENGTH"] = 20
    client = app.test_client()
    response = client.post(
        "/api/auth/register",
        json={"email": "large@example.com", "password": "x" * 100},
    )
    assert response.status_code == 413
    assert response.get_json()["code"] == "request_too_large"
