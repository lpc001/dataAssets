from app.models.role_data_scope import RoleDataScope


def _create_role(client):
    return client.post("/api/v1/roles", json={"name": "管理员", "code": "TEST_ROLE"}).json()


def test_get_scope_default_none(client):
    role = _create_role(client)
    resp = client.get(f"/api/v1/roles/{role['id']}/data-scope")
    assert resp.status_code == 200
    assert resp.json() == {
        "id": 0,
        "role_id": role["id"],
        "scope_type": "ALL",
        "custom_org_ids": "",
    }


def test_upsert_scope_all(client):
    role = _create_role(client)
    resp = client.put(
        f"/api/v1/roles/{role['id']}/data-scope",
        json={"scope_type": "ALL", "custom_org_ids": []},
    )
    assert resp.status_code == 200
    assert resp.json()["scope_type"] == "ALL"


def test_upsert_scope_custom(client, db_session):
    role = _create_role(client)
    resp = client.put(
        f"/api/v1/roles/{role['id']}/data-scope",
        json={"scope_type": "CUSTOM", "custom_org_ids": [1, 3, 5]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["scope_type"] == "CUSTOM"
    assert body["custom_org_ids"] == "1,3,5"

    record = db_session.query(RoleDataScope).filter(RoleDataScope.role_id == role["id"]).first()
    assert record.custom_org_ids == "1,3,5"


def test_upsert_scope_invalid_type(client):
    role = _create_role(client)
    resp = client.put(
        f"/api/v1/roles/{role['id']}/data-scope",
        json={"scope_type": "INVALID", "custom_org_ids": []},
    )
    assert resp.status_code == 422


def test_upsert_overwrites_previous(client):
    role = _create_role(client)
    client.put(
        f"/api/v1/roles/{role['id']}/data-scope",
        json={"scope_type": "CUSTOM", "custom_org_ids": [1, 3]},
    )
    resp = client.put(
        f"/api/v1/roles/{role['id']}/data-scope",
        json={"scope_type": "ORG_ONLY", "custom_org_ids": []},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["scope_type"] == "ORG_ONLY"
    assert body["custom_org_ids"] == ""
