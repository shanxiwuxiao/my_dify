def test_register_login_logout_and_me(app) -> None:
    client = app.test_client()
    assert client.get("/api/auth/me").status_code == 401

    response = client.post(
        "/api/auth/register",
        json={"email": " User@Example.com ", "password": "password123"},
    )
    assert response.status_code == 201
    assert response.get_json()["email"] == "user@example.com"
    assert client.get("/api/auth/me").status_code == 200

    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401
    assert client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    ).status_code == 200


def test_users_cannot_access_each_others_apps(app) -> None:
    first = app.test_client()
    second = app.test_client()
    first.post("/api/auth/register", json={"email": "first@example.com", "password": "password123"})
    created = first.post("/api/apps", json={"name": "Private"}).get_json()
    second.post("/api/auth/register", json={"email": "second@example.com", "password": "password123"})

    assert second.get("/api/apps").get_json()["total"] == 0
    assert second.get(f"/api/apps/{created['id']}").status_code == 404
    assert second.delete(f"/api/apps/{created['id']}").status_code == 404


def test_duplicate_email_and_invalid_login(app) -> None:
    client = app.test_client()
    payload = {"email": "user@example.com", "password": "password123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={**payload, "password": "wrongpass"}).status_code == 401
