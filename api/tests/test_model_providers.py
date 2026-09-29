def test_provider_credentials_are_encrypted_and_never_returned(client, app) -> None:
    response = client.post("/api/model-providers", json={
        "name": "DeepSeek", "base_url": "https://api.deepseek.com/v1",
        "api_key": "secret-key", "default_model": "deepseek-chat",
    })
    assert response.status_code == 201
    assert response.get_json()["api_key_masked"] == "••••••••"
    assert "secret-key" not in response.get_data(as_text=True)

    from my_dify.models.model_provider import ModelProviderModel
    from my_dify.extensions.database import db
    with app.app_context():
        stored = db.session.execute(db.select(ModelProviderModel)).scalar_one()
        assert stored.api_key_encrypted != "secret-key"


def test_providers_are_isolated_between_users(app) -> None:
    first, second = app.test_client(), app.test_client()
    first.post("/api/auth/register", json={"email": "p1@example.com", "password": "password123"})
    second.post("/api/auth/register", json={"email": "p2@example.com", "password": "password123"})
    created = first.post("/api/model-providers", json={"name": "One", "base_url": "https://example.com/v1", "api_key": "key", "default_model": "model"}).get_json()
    assert second.get("/api/model-providers").get_json()["total"] == 0
    assert second.delete(f"/api/model-providers/{created['id']}").status_code == 404


def test_application_can_only_bind_owned_provider(app) -> None:
    first, second = app.test_client(), app.test_client()
    first.post("/api/auth/register", json={"email": "owner@example.com", "password": "password123"})
    provider = first.post("/api/model-providers", json={"name": "Owned", "base_url": "https://example.com/v1", "api_key": "key", "default_model": "model"}).get_json()
    created = first.post("/api/apps", json={"name": "Bound", "provider_id": provider["id"]})
    assert created.status_code == 201
    assert created.get_json()["provider_id"] == provider["id"]

    second.post("/api/auth/register", json={"email": "intruder@example.com", "password": "password123"})
    denied = second.post("/api/apps", json={"name": "Denied", "provider_id": provider["id"]})
    assert denied.status_code == 404
