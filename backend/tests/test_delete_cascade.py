"""删除用户/角色时先清关联表，避免外键约束报 500。"""


def _create_user(client, username="job1"):
    resp = client.post(
        "/api/v1/users", json={"username": username, "name": "待删用户", "password": "secret123"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_delete_user_with_roles(client):
    user = _create_user(client)
    role = client.post("/api/v1/roles", json={"name": "待删角色", "code": "DELU"}).json()
    assert client.put(f"/api/v1/users/{user['id']}/roles", json={"role_ids": [role["id"]]}).status_code == 200

    resp = client.delete(f"/api/v1/users/{user['id']}")
    assert resp.status_code == 204, resp.text
    assert client.get(f"/api/v1/users/{user['id']}").status_code == 404
    # 角色还在，只是没有成员了
    assert client.get(f"/api/v1/roles/{role['id']}").status_code == 200


def test_delete_role_with_users_scope_and_permissions(client):
    user = _create_user(client, username="job2")
    role = client.post("/api/v1/roles", json={"name": "待删角色2", "code": "DELR"}).json()

    assert client.put(f"/api/v1/users/{user['id']}/roles", json={"role_ids": [role["id"]]}).status_code == 200
    assert (
        client.put(
            f"/api/v1/roles/{role['id']}/data-scope",
            json={"scope_type": "ORG_ONLY", "custom_org_ids": []},
        ).status_code
        == 200
    )
    assert (
        client.put(
            f"/api/v1/roles/{role['id']}/permissions",
            json={"permissions": ["system:user"]},
        ).status_code
        == 200
    )

    resp = client.delete(f"/api/v1/roles/{role['id']}")
    assert resp.status_code == 204, resp.text
    assert client.get(f"/api/v1/roles/{role['id']}").status_code == 404
    # 用户还在，只是失去了该角色
    assert client.get(f"/api/v1/users/{user['id']}/roles").json() == []
