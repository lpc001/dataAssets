def test_create_and_list_role(client):
    resp = client.post(
        "/api/v1/roles",
        json={"name": "管理员", "code": "TEST_ROLE"},
    )
    assert resp.status_code == 201
    assert resp.json()["code"] == "TEST_ROLE"

    resp = client.get("/api/v1/roles")
    assert resp.status_code == 200
    assert "TEST_ROLE" in [r["code"] for r in resp.json()]


def test_create_duplicate_code(client):
    client.post("/api/v1/roles", json={"name": "管理员", "code": "TEST_ROLE"})
    resp = client.post("/api/v1/roles", json={"name": "管理员2", "code": "TEST_ROLE"})
    assert resp.status_code == 400


def test_update_role(client):
    role = client.post("/api/v1/roles", json={"name": "管理员", "code": "TEST_ROLE"}).json()
    resp = client.put(f"/api/v1/roles/{role['id']}", json={"name": "超级管理员"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "超级管理员"


def test_delete_role(client):
    role = client.post("/api/v1/roles", json={"name": "管理员", "code": "TEST_ROLE"}).json()
    resp = client.delete(f"/api/v1/roles/{role['id']}")
    assert resp.status_code == 204
    assert "TEST_ROLE" not in [r["code"] for r in client.get("/api/v1/roles").json()]
