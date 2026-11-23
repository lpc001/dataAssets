"""数据源配置相关用例。"""

from app.core.crypto import decrypt_text, encrypt_text


def test_crypto_roundtrip():
    cipher = encrypt_text("52youforever")
    assert cipher != "52youforever"
    assert "52youforever" not in cipher
    assert decrypt_text(cipher) == "52youforever"


def test_decrypt_invalid_returns_empty():
    assert decrypt_text("not-a-valid-token") == ""
    assert decrypt_text("") == ""


def test_create_datasource_does_not_echo_password(client):
    resp = client.post(
        "/api/v1/datasources",
        json={
            "name": "本地 water_dw",
            "host": "127.0.0.1",
            "port": 1,
            "database_name": "water_dw",
            "schema_filter": "cdm,cdm_mock",
            "username": "postgres",
            "password": "secret-pwd",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "password" not in body
    assert "password_cipher" not in body
    assert body["name"] == "本地 water_dw"
    # 端口 1 不可达，只读校验应为 False
    assert body["readonly_verified"] is False


def test_duplicate_datasource_name_conflict(client):
    payload = {
        "name": "重复源",
        "host": "127.0.0.1",
        "port": 1,
        "database_name": "db",
        "schema_filter": "public",
        "username": "u",
        "password": "p",
    }
    assert client.post("/api/v1/datasources", json=payload).status_code == 201
    assert client.post("/api/v1/datasources", json=payload).status_code == 409


def test_update_datasource_without_password_keeps_it(client, db_session):
    from app.models.datasource import DataSource

    created = client.post(
        "/api/v1/datasources",
        json={
            "name": "改名测试",
            "host": "127.0.0.1",
            "port": 1,
            "database_name": "db",
            "schema_filter": "public",
            "username": "u",
            "password": "p1",
        },
    ).json()

    resp = client.put(f"/api/v1/datasources/{created['id']}", json={"name": "改名后"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "改名后"

    row = db_session.get(DataSource, created["id"])
    assert decrypt_text(row.password_cipher) == "p1"
