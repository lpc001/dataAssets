def test_login_success(anon_client):
    resp = anon_client.post(
        "/api/v1/auth/login",
        data={"username": "test_admin", "password": "secret123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(anon_client):
    resp = anon_client.post(
        "/api/v1/auth/login",
        data={"username": "test_admin", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_login_unknown_user(anon_client):
    resp = anon_client.post(
        "/api/v1/auth/login",
        data={"username": "nobody", "password": "secret123"},
    )
    assert resp.status_code == 401


def test_unauthenticated_access_denied(anon_client):
    resp = anon_client.get("/api/v1/users")
    assert resp.status_code == 401


def test_authenticated_access_ok(client):
    resp = client.get("/api/v1/users")
    assert resp.status_code == 200
