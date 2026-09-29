from flask.testing import FlaskClient

from my_dify.extensions.database import db
from my_dify.models.message import MessageModel


def create_application(client: FlaskClient) -> dict:
    response = client.post("/api/apps", json={"name": "Python 助手"})
    assert response.status_code == 201
    return response.get_json()


def create_conversation(client: FlaskClient, app_id: str, name="学习 Python") -> dict:
    response = client.post(
        f"/api/apps/{app_id}/conversations",
        json={"name": name},
    )
    assert response.status_code == 201
    return response.get_json()


def test_create_conversation(client: FlaskClient) -> None:
    application = create_application(client)

    response = client.post(
        f"/api/apps/{application['id']}/conversations",
        json={"name": "  学习 Python  "},
    )

    assert response.status_code == 201
    assert response.get_json()["app_id"] == application["id"]
    assert response.get_json()["name"] == "学习 Python"


def test_create_conversation_uses_default_name(client: FlaskClient) -> None:
    application = create_application(client)

    response = client.post(
        f"/api/apps/{application['id']}/conversations",
        json={},
    )

    assert response.status_code == 201
    assert response.get_json()["name"] == "New conversation"


def test_create_conversation_returns_404_for_missing_app(
    client: FlaskClient,
) -> None:
    response = client.post("/api/apps/missing/conversations", json={})

    assert response.status_code == 404
    assert response.get_json()["code"] == "app_not_found"


def test_list_and_get_conversations(client: FlaskClient) -> None:
    application = create_application(client)
    first = create_conversation(client, application["id"], "会话一")
    second = create_conversation(client, application["id"], "会话二")

    response = client.get(f"/api/apps/{application['id']}/conversations")

    assert response.status_code == 200
    assert response.get_json()["total"] == 2
    assert {item["id"] for item in response.get_json()["items"]} == {
        first["id"],
        second["id"],
    }
    assert client.get(f"/api/conversations/{first['id']}").status_code == 200


def test_get_missing_conversation_returns_404(client: FlaskClient) -> None:
    response = client.get("/api/conversations/missing")

    assert response.status_code == 404
    assert response.get_json()["code"] == "conversation_not_found"


def test_rename_conversation(client: FlaskClient) -> None:
    application = create_application(client)
    conversation = create_conversation(client, application["id"])

    response = client.patch(
        f"/api/conversations/{conversation['id']}",
        json={"name": "  新名称  "},
    )

    assert response.status_code == 200
    assert response.get_json()["name"] == "新名称"
    saved = client.get(f"/api/conversations/{conversation['id']}").get_json()
    assert saved["name"] == "新名称"


def test_rename_conversation_rejects_invalid_name(client: FlaskClient) -> None:
    application = create_application(client)
    conversation = create_conversation(client, application["id"])

    response = client.patch(
        f"/api/conversations/{conversation['id']}",
        json={"name": "   "},
    )

    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_request"


def test_rename_missing_conversation_returns_404(client: FlaskClient) -> None:
    response = client.patch(
        "/api/conversations/missing",
        json={"name": "新名称"},
    )

    assert response.status_code == 404
    assert response.get_json()["code"] == "conversation_not_found"


def test_delete_conversation(client: FlaskClient) -> None:
    application = create_application(client)
    conversation = create_conversation(client, application["id"])

    response = client.delete(f"/api/conversations/{conversation['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/conversations/{conversation['id']}").status_code == 404


def test_delete_conversation_cascades_messages(client: FlaskClient, app) -> None:
    application = create_application(client)
    conversation = create_conversation(client, application["id"])
    assert client.post(
        f"/api/conversations/{conversation['id']}/messages",
        json={"message": "你好"},
    ).status_code == 200

    client.delete(f"/api/conversations/{conversation['id']}")

    with app.app_context():
        assert db.session.query(MessageModel).count() == 0
