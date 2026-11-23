"""功能权限：模块级权限点、默认权限、ADMIN 绕过、个人中心。"""


def _create_user(client, username="op1", password="secret123", name="操作员"):
    resp = client.post(
        "/api/v1/users",
        json={"username": username, "name": name, "password": password},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_role(client, code="OPERATOR", name="操作员"):
    resp = client.post("/api/v1/roles", json={"name": name, "code": code})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _bind(client, user_id, role_id):
    resp = client.put(f"/api/v1/users/{user_id}/roles", json={"role_ids": [role_id]})
    assert resp.status_code == 200, resp.text


def _login(username="op1", password="secret123"):
    from fastapi.testclient import TestClient

    from app.main import app

    c = TestClient(app)
    resp = c.post("/api/v1/auth/login", data={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    c.headers["Authorization"] = f"Bearer {resp.json()['access_token']}"
    return c


def test_new_role_has_no_permission_by_default(client):
    """没有任何权限记录的角色：系统管理一律 403，但能改自己的资料。"""
    user = _create_user(client)
    role = _create_role(client)
    _bind(client, user["id"], role["id"])

    op = _login()
    assert op.get("/api/v1/organizations").status_code == 403
    assert op.get("/api/v1/users").status_code == 403
    assert op.get("/api/v1/roles").status_code == 403
    assert op.put("/api/v1/brand", json={"name": "X"}).status_code == 403
    assert op.get("/api/v1/users/me").status_code == 200

    me = op.get("/api/v1/auth/me").json()
    assert me["permissions"] == []
    assert me["is_admin"] is False


def test_grant_permissions_takes_effect(client):
    user = _create_user(client)
    role = _create_role(client)
    _bind(client, user["id"], role["id"])

    resp = client.put(
        f"/api/v1/roles/{role['id']}/permissions", json={"permissions": ["system:user"]}
    )
    assert resp.status_code == 200, resp.text

    op = _login()
    assert op.get("/api/v1/users").status_code == 200
    # 读角色允许（分配用户角色要用），写角色仍需 system:role
    assert op.get("/api/v1/roles").status_code == 200
    assert op.post("/api/v1/roles", json={"name": "X", "code": "X"}).status_code == 403


def test_admin_bypasses_permission(client):
    me = client.get("/api/v1/auth/me").json()
    assert me["is_admin"] is True
    assert client.get("/api/v1/users").status_code == 200
    assert client.get("/api/v1/roles").status_code == 200


def test_permission_endpoints_require_login(anon_client):
    assert anon_client.get("/api/v1/users").status_code == 401
    assert anon_client.get("/api/v1/roles").status_code == 401
