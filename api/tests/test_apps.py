from flask.testing import FlaskClient


def create_application(client: FlaskClient, **overrides):
    payload = {
        "name": "Python 助手",
        "description": "帮助学习 Python",
        "system_prompt": "你是一名耐心的 Python 老师",
        "model_name": "deepseek-flash",
        "temperature": 0.5,
    }
    payload.update(overrides)
    return client.post("/api/apps", json=payload)


def test_create_application(client: FlaskClient) -> None:
    response = create_application(client)
    body = response.get_json()

    assert response.status_code == 201
    assert len(body["id"]) == 36
    assert body["name"] == "Python 助手"
    assert body["temperature"] == 0.5
    assert body["created_at"]
    assert body["updated_at"]


def test_create_application_uses_defaults(client: FlaskClient) -> None:
    response = client.post("/api/apps", json={"name": "默认应用"})

    assert response.status_code == 201
    assert response.get_json()["description"] == ""
    assert response.get_json()["model_name"] == "deepseek-flash"
    assert response.get_json()["temperature"] == 0.7


def test_create_application_strips_name(client: FlaskClient) -> None:
    response = client.post("/api/apps", json={"name": "  Python 助手  "})

    assert response.status_code == 201
    assert response.get_json()["name"] == "Python 助手"


def test_create_application_rejects_empty_name(client: FlaskClient) -> None:
    response = client.post("/api/apps", json={"name": "   "})

    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_request"


def test_create_application_rejects_invalid_temperature(client: FlaskClient) -> None:
    response = client.post("/api/apps", json={"name": "应用", "temperature": 2.1})

    assert response.status_code == 400


def test_list_applications_is_empty(client: FlaskClient) -> None:
    response = client.get("/api/apps")

    assert response.status_code == 200
    assert response.get_json() == {"items": [], "total": 0}


def test_list_applications_returns_created_apps(client: FlaskClient) -> None:
    create_application(client, name="应用一")
    create_application(client, name="应用二")

    response = client.get("/api/apps")
    body = response.get_json()

    assert response.status_code == 200
    assert body["total"] == 2
    assert [item["name"] for item in body["items"]] == ["应用二", "应用一"]


def test_get_application(client: FlaskClient) -> None:
    created = create_application(client).get_json()

    response = client.get(f"/api/apps/{created['id']}")

    assert response.status_code == 200
    assert response.get_json()["id"] == created["id"]


def test_get_missing_application_returns_404(client: FlaskClient) -> None:
    response = client.get("/api/apps/missing")

    assert response.status_code == 404
    assert response.get_json() == {
        "code": "app_not_found",
        "message": "Application not found",
    }


def test_update_application_only_changes_submitted_fields(client: FlaskClient) -> None:
    created = create_application(client).get_json()

    response = client.patch(
        f"/api/apps/{created['id']}",
        json={"name": "新名称"},
    )
    body = response.get_json()

    assert response.status_code == 200
    assert body["name"] == "新名称"
    assert body["system_prompt"] == created["system_prompt"]
    assert body["temperature"] == created["temperature"]


def test_update_application_rejects_empty_payload(client: FlaskClient) -> None:
    created = create_application(client).get_json()

    response = client.patch(f"/api/apps/{created['id']}", json={})

    assert response.status_code == 400


def test_update_missing_application_returns_404(client: FlaskClient) -> None:
    response = client.patch("/api/apps/missing", json={"name": "新名称"})

    assert response.status_code == 404


def test_delete_application(client: FlaskClient) -> None:
    created = create_application(client).get_json()

    response = client.delete(f"/api/apps/{created['id']}")

    assert response.status_code == 204
    assert response.get_data() == b""
    assert client.get(f"/api/apps/{created['id']}").status_code == 404


def test_delete_missing_application_returns_404(client: FlaskClient) -> None:
    response = client.delete("/api/apps/missing")

    assert response.status_code == 404


def test_publish_creates_immutable_incrementing_versions(client: FlaskClient) -> None:
    created = create_application(client, system_prompt="version one") .get_json()

    first = client.post(f"/api/apps/{created['id']}/publish")
    assert first.status_code == 201
    assert first.get_json()["version"] == 1
    assert first.get_json()["system_prompt"] == "version one"

    client.patch(f"/api/apps/{created['id']}", json={"system_prompt": "version two"})
    second = client.post(f"/api/apps/{created['id']}/publish")
    versions = client.get(f"/api/apps/{created['id']}/versions").get_json()["items"]

    assert second.get_json()["version"] == 2
    assert [item["version"] for item in versions] == [2, 1]
    assert versions[1]["system_prompt"] == "version one"


def test_create_application_rejects_non_json_request(client: FlaskClient) -> None:
    response = client.post("/api/apps", data="hello", content_type="text/plain")

    assert response.status_code == 400
