def _create_user(client, username="u1"):
    return client.post(
        "/api/v1/users",
        json={"username": username, "name": username, "password": "secret123"},
    ).json()


def _create_role(client, code="TEST_ROLE", name="管理员"):
    return client.post("/api/v1/roles", json={"name": name, "code": code}).json()


def test_get_user_roles_empty(client):
    user = _create_user(client)
    resp = client.get(f"/api/v1/users/{user['id']}/roles")
    assert resp.status_code == 200
    assert resp.json() == []


def test_set_user_roles(client):
    user = _create_user(client)
    r1 = _create_role(client, "ROLE_A", "管理员")
    r2 = _create_role(client, "OPERATOR", "操作员")

    resp = client.put(
        f"/api/v1/users/{user['id']}/roles",
        json={"role_ids": [r1["id"], r2["id"]]},
    )
    assert resp.status_code == 200
    assert {r["id"] for r in resp.json()} == {r1["id"], r2["id"]}


def test_set_user_roles_overwrites(client):
    user = _create_user(client)
    r1 = _create_role(client, "ROLE_A", "管理员")
    r2 = _create_role(client, "OPERATOR", "操作员")

    client.put(f"/api/v1/users/{user['id']}/roles", json={"role_ids": [r1["id"], r2["id"]]})
    resp = client.put(f"/api/v1/users/{user['id']}/roles", json={"role_ids": [r2["id"]]})
    assert resp.status_code == 200
    assert {r["id"] for r in resp.json()} == {r2["id"]}


def test_set_user_roles_nonexistent_user(client):
    resp = client.put("/api/v1/users/9999/roles", json={"role_ids": []})
    assert resp.status_code == 404
