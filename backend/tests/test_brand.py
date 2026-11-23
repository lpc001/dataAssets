# -*- coding: utf-8 -*-
"""品牌配置测试：公开读取、权限、更新、校验、恢复默认。"""
from app.services import brand as brand_svc


def test_brand_public_read(anon_client):
    body = anon_client.get("/api/v1/brand").json()
    assert body["name"]
    assert body["logo"].startswith("data:image/") or body["logo"].startswith("data:image/svg")


def test_brand_update_requires_permission(db_session, anon_client):
    resp = anon_client.put("/api/v1/brand", json={"name": "X"})
    assert resp.status_code == 401


def test_brand_update_and_reset(client, anon_client):
    seed = client.get("/api/v1/brand").json()
    resp = client.put(
        "/api/v1/brand",
        json={"name": "银河联邦水务", "subtitle": "指标管理平台", "logo": "data:image/png;base64,AAAA"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "银河联邦水务"
    assert body["logo"].startswith("data:image/png")

    # 公开接口也能读到最新值
    assert anon_client.get("/api/v1/brand").json()["name"] == "银河联邦水务"

    reset = client.post("/api/v1/brand/reset").json()
    assert reset["name"] == brand_svc.DEFAULT_NAME
    assert reset["logo"] == brand_svc.DEFAULT_LOGO


def test_brand_rejects_non_image_logo(client):
    resp = client.put("/api/v1/brand", json={"logo": "http://example.com/logo.png"})
    assert resp.status_code == 400
    assert "图片" in resp.json()["detail"]


def test_brand_ignores_empty_logo_falls_back(client):
    client.put("/api/v1/brand", json={"logo": ""})
    body = client.get("/api/v1/brand").json()
    assert body["logo"] == brand_svc.DEFAULT_LOGO
