"""指标创建、校验与发布用例。"""

from datetime import datetime

from app.models.asset import Asset
from app.models.asset_column import AssetColumn
from app.models.resource_column import ResourceColumn
from app.models.resource_table import ResourceTable


def _seed_column(db):
    resource = ResourceTable(
        datasource_id=1,
        schema_name="cdm",
        table_name="dim_bank",
        table_comment="代收银行",
        row_count=3,
        column_count=3,
    )
    db.add(resource)
    db.flush()
    column = ResourceColumn(
        resource_table_id=resource.id, column_name="bank_code", ordinal=1, data_type="text"
    )
    db.add(column)
    db.flush()
    asset = Asset(
        resource_table_id=resource.id,
        asset_code="DA00001",
        asset_name="代收银行",
        domain_code="mkt",
        status="PUBLISHED",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(asset)
    db.flush()
    asset_column = AssetColumn(
        asset_id=asset.id,
        resource_column_id=column.id,
        column_name="bank_code",
        ordinal=1,
        sensitive_level="L1",
    )
    db.add(asset_column)
    db.commit()
    return asset_column


def _payload(column_id, **overrides):
    payload = {
        "indicator_name": "银行数量",
        "indicator_def": "在册代收银行数量",
        "formula": "count(bank_code)",
        "unit": "个",
        "cycle": "月",
        "source_asset_column_id": column_id,
    }
    payload.update(overrides)
    return payload


def test_create_and_publish_indicator(client, db_session):
    column = _seed_column(db_session)
    created = client.post("/api/v1/indicators", json=_payload(column.id)).json()
    assert len(created["indicator_code"]) == 7 and created["indicator_code"][:2].isalpha()
    assert created["status"] == "DRAFT"
    assert created["source_path"]["table_name"] == "dim_bank"
    assert [i["rule_code"] for i in created["issues"]] == ["R06"]

    published = client.post(f"/api/v1/indicators/{created['id']}/publish")
    assert published.status_code == 200
    assert published.json()["status"] == "PUBLISHED"


def test_formula_block_prevents_publish(client, db_session):
    column = _seed_column(db_session)
    created = client.post(
        "/api/v1/indicators", json=_payload(column.id, formula="实收/应收")
    ).json()
    codes = {i["rule_code"] for i in created["issues"] if i["severity"] == "BLOCK"}
    assert "R05" in codes

    resp = client.post(f"/api/v1/indicators/{created['id']}/publish")
    assert resp.status_code == 409


def test_domain_mismatch_blocks(client, db_session):
    column = _seed_column(db_session)
    created = client.post(
        "/api/v1/indicators", json=_payload(column.id, domain_code="svc")
    ).json()
    codes = {i["rule_code"] for i in created["issues"] if i["severity"] == "BLOCK"}
    assert "R11" in codes
