def _create_role(client):
    return client.post("/api/v1/roles", json={"name": "管理员", "code": "TEST_ROLE"}).json()


def _create_user(client, username="u1"):
    return client.post(
        "/api/v1/users",
        json={"username": username, "name": username, "password": "secret123"},
    ).json()


def test_list_role_users_empty(client):
    role = _create_role(client)
    resp = client.get(f"/api/v1/roles/{role['id']}/users")
    assert resp.status_code == 200
    assert resp.json() == []


def test_set_role_users(client):
    role = _create_role(client)
    u1 = _create_user(client, "u1")
    u2 = _create_user(client, "u2")

    resp = client.put(
        f"/api/v1/roles/{role['id']}/users",
        json={"user_ids": [u1["id"], u2["id"]]},
    )
    assert resp.status_code == 200
    assert {u["id"] for u in resp.json()} == {u1["id"], u2["id"]}


def test_set_role_users_overwrites(client):
    role = _create_role(client)
    u1 = _create_user(client, "u1")
    u2 = _create_user(client, "u2")

    client.put(f"/api/v1/roles/{role['id']}/users", json={"user_ids": [u1["id"], u2["id"]]})
    resp = client.put(f"/api/v1/roles/{role['id']}/users", json={"user_ids": [u2["id"]]})
    assert resp.status_code == 200
    assert {u["id"] for u in resp.json()} == {u2["id"]}


def test_set_role_users_nonexistent_role(client):
    resp = client.put("/api/v1/roles/9999/users", json={"user_ids": []})
    assert resp.status_code == 404
