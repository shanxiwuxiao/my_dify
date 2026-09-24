from flask.testing import FlaskClient


def test_health(client: FlaskClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "service": "my-dify-api",
        "status": "ok",
    }
