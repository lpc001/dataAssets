def test_create_and_list_organization(client):
    resp = client.post(
        "/api/v1/organizations",
        json={"code": "GROUP", "name": "福建水投集团", "type": "GROUP"},
    )
    assert resp.status_code == 201
    assert resp.json()["code"] == "GROUP"

    resp = client.get("/api/v1/organizations")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_create_child_organization(client):
    parent = client.post(
        "/api/v1/organizations",
        json={"code": "GROUP", "name": "福建水投集团", "type": "GROUP"},
    ).json()

    resp = client.post(
        "/api/v1/organizations",
        json={"code": "WS001", "name": "某水司", "type": "WATER_COMPANY", "parent_id": parent["id"]},
    )
    assert resp.status_code == 201
    assert resp.json()["parent_id"] == parent["id"]


def test_get_and_update_organization(client):
    org = client.post(
        "/api/v1/organizations",
        json={"code": "GROUP", "name": "福建水投集团", "type": "GROUP"},
    ).json()

    resp = client.get(f"/api/v1/organizations/{org['id']}")
    assert resp.status_code == 200

    resp = client.put(
        f"/api/v1/organizations/{org['id']}",
        json={"name": "福建水投集团（更名）"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "福建水投集团（更名）"


def test_delete_organization(client):
    org = client.post(
        "/api/v1/organizations",
        json={"code": "GROUP", "name": "福建水投集团", "type": "GROUP"},
    ).json()

    resp = client.delete(f"/api/v1/organizations/{org['id']}")
    assert resp.status_code == 204

    resp = client.get(f"/api/v1/organizations/{org['id']}")
    assert resp.status_code == 404
