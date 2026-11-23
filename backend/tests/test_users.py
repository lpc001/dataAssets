from app.models.user import User


def _create_org(client) -> int:
    return client.post(
        "/api/v1/organizations",
        json={"code": "GROUP", "name": "福建水投集团", "type": "GROUP"},
    ).json()["id"]


def test_create_user_password_hashed(client, db_session):
    org_id = _create_org(client)
    resp = client.post(
        "/api/v1/users",
        json={"username": "admin", "name": "管理员", "password": "secret123", "org_id": org_id},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "password" not in body
    assert "password_hash" not in body

    user = db_session.query(User).filter(User.username == "admin").first()
    assert user.password_hash != "secret123"


def test_create_duplicate_username(client):
    client.post(
        "/api/v1/users",
        json={"username": "admin", "name": "管理员", "password": "secret123"},
    )
    resp = client.post(
        "/api/v1/users",
        json={"username": "admin", "name": "管理员2", "password": "secret123"},
    )
    assert resp.status_code == 400


def test_update_user_password(client, db_session):
    client.post(
        "/api/v1/users",
        json={"username": "admin", "name": "管理员", "password": "secret123"},
    )
    user = db_session.query(User).filter(User.username == "admin").first()

    resp = client.put(f"/api/v1/users/{user.id}", json={"password": "newpass456"})
    assert resp.status_code == 200

    db_session.refresh(user)
    assert user.password_hash != "newpass456"


def test_delete_user(client):
    client.post(
        "/api/v1/users",
        json={"username": "admin", "name": "管理员", "password": "secret123"},
    )
    users = client.get("/api/v1/users").json()
    admin_ids = [u["id"] for u in users if u["username"] == "admin"]
    assert len(admin_ids) == 1

    resp = client.delete(f"/api/v1/users/{admin_ids[0]}")
    assert resp.status_code == 204

    remaining = client.get("/api/v1/users").json()
    assert all(u["username"] != "admin" for u in remaining)
    assert any(u["username"] == "test_admin" for u in remaining)
