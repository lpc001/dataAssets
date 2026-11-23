"""资源池采集、版本记录与资产登记用例。"""

import pytest

from app.adapters.base import RemoteColumn, RemoteTable
from app.core.crypto import encrypt_text
from app.models.asset import Asset
from app.models.datasource import DataSource
from app.models.meta_change import MetaChange
from app.models.resource_column import ResourceColumn
from app.models.resource_table import ResourceTable
from app.services.classify import classify_table, detect_temp
from app.schemas.catalog import RegisterItem
from app.services.register import register_resources
from app.services.sync import sync_datasource


@pytest.mark.parametrize(
    "name,expected",
    [
        ("dim_cust", ("DIM", None, "C")),
        ("dwd_mkt_meter_reading", ("DWD", "mkt", "A")),
        ("dws_svc_hotline_day", ("DWS", "svc", "D")),
        ("dws_nrw_summary", ("DWS", None, "D")),
        ("tmp_import_202601", ("OTHER", None, None)),
    ],
)
def test_classify_table(name, expected):
    assert classify_table(name) == expected


def test_detect_temp():
    assert detect_temp("tmp_reading") is True
    assert detect_temp("reading_bak") is True
    assert detect_temp("dwd_mkt_billing") is False


class FakeAdapter:
    def __init__(self, tables):
        self.tables = tables

    def test_connection(self):
        return True, "ok"

    def is_readonly(self):
        return True

    def fetch_tables(self, schemas):
        return self.tables


def _table(name, schema="cdm", row_count=10, columns=None, comment=None):
    cols = columns or [
        RemoteColumn("id", 1, "bigint", False, None, "主键", True),
        RemoteColumn("ds", 2, "string", True, None, "分区", False),
    ]
    return RemoteTable(
        schema=schema, name=name, comment=comment or f"{name} 注释", row_count=row_count, columns=cols
    )


def _make_datasource(db):
    ds = DataSource(
        name="测试源",
        db_type="postgresql",
        host="127.0.0.1",
        port=1,
        database_name="db",
        schema_filter="cdm",
        username="u",
        password_cipher=encrypt_text("p"),
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


def test_sync_writes_resource_pool_and_version(db_session):
    ds = _make_datasource(db_session)

    version = sync_datasource(db_session, ds, FakeAdapter([_table("dwd_mkt_billing"), _table("dim_cust")]), operator="tester")

    assert version.status == "SUCCESS"
    assert version.table_added == 2
    assert version.column_added == 4
    assert version.version_no == 1

    billing = db_session.query(ResourceTable).filter_by(table_name="dwd_mkt_billing").one()
    assert (billing.suggested_layer, billing.suggested_domain, billing.suggested_trace) == ("DWD", "mkt", "A")
    assert billing.column_count == 2
    cust = db_session.query(ResourceTable).filter_by(table_name="dim_cust").one()
    assert (cust.suggested_layer, cust.suggested_domain, cust.suggested_trace) == ("DIM", None, "C")

    changes = db_session.query(MetaChange).filter_by(version_id=version.id).all()
    assert len(changes) == 6  # 2 张表 + 4 个字段
    assert {c.change_type for c in changes} == {"ADD"}

    # 资源池不产生资产
    assert db_session.query(Asset).count() == 0


def test_sync_second_version_records_changes(db_session):
    ds = _make_datasource(db_session)
    sync_datasource(db_session, ds, FakeAdapter([_table("dwd_mkt_billing")]))

    changed = _table("dwd_mkt_billing", row_count=12, comment="新的注释")
    version2 = sync_datasource(db_session, ds, FakeAdapter([changed]))

    assert version2.version_no == 2
    assert version2.table_changed == 1
    fields = {c.field_name for c in db_session.query(MetaChange).filter_by(version_id=version2.id)}
    assert "table_comment" in fields

    version3 = sync_datasource(db_session, ds, FakeAdapter([changed]))
    assert (version3.table_added, version3.table_changed, version3.table_dropped) == (0, 0, 0)
    assert db_session.query(MetaChange).filter_by(version_id=version3.id).count() == 0


def test_sync_marks_dropped_tables(db_session):
    ds = _make_datasource(db_session)
    sync_datasource(db_session, ds, FakeAdapter([_table("dwd_mkt_billing"), _table("dwd_mkt_payment")]))
    version = sync_datasource(db_session, ds, FakeAdapter([_table("dwd_mkt_billing")]))

    assert version.table_dropped == 1
    payment = db_session.query(ResourceTable).filter_by(table_name="dwd_mkt_payment").one()
    assert payment.remote_status == "MISSING"


def test_register_creates_asset_with_columns(db_session):
    ds = _make_datasource(db_session)
    sync_datasource(db_session, ds, FakeAdapter([_table("dwd_mkt_billing")]))
    resource = db_session.query(ResourceTable).filter_by(table_name="dwd_mkt_billing").one()

    created = register_resources(
        db_session, ds.id, [RegisterItem(resource_id=resource.id, asset_name="计费明细")], operator="tester"
    )

    assert len(created) == 1
    asset = created[0]
    assert asset.status == "PUBLISHED"
    assert asset.asset_code.startswith("DA")
    assert asset.asset_name == "计费明细"
    assert asset.domain_code == "mkt"
    assert len(asset_columns(db_session, asset.id)) == 2

    # 重复登记不产生新资产
    again = register_resources(
        db_session, ds.id, [RegisterItem(resource_id=resource.id)], operator="tester"
    )
    assert again == []
    assert db_session.query(Asset).count() == 1


def test_register_group_defaults_and_patch(db_session):
    from app.models.asset import Asset

    ds = _make_datasource(db_session)
    sync_datasource(db_session, ds, FakeAdapter([_table("dim_cust"), _table("dws_nrw_summary")]))
    resources = {
        r.table_name: r
        for r in db_session.query(ResourceTable).filter(
            ResourceTable.table_name.in_(["dim_cust", "dws_nrw_summary"])
        )
    }

    created = register_resources(
        db_session,
        ds.id,
        [RegisterItem(resource_id=resources["dim_cust"].id), RegisterItem(resource_id=resources["dws_nrw_summary"].id)],
    )
    groups = {a.asset_name: (a.group_type, a.domain_code) for a in created}
    assert groups["dim_cust 注释"] == ("PUBLIC", None)
    assert groups["dws_nrw_summary 注释"] == ("TOPIC", None)

    # 归为业务域时清空原有归类限制
    asset = db_session.query(Asset).filter_by(resource_table_id=resources["dim_cust"].id).one()
    from app.schemas.catalog import AssetPatch
    from app.crud import asset as asset_crud

    asset_crud.patch(db_session, asset, AssetPatch(group_type="DOMAIN", domain_code="mkt"))
    db_session.refresh(asset)
    assert (asset.group_type, asset.domain_code) == ("DOMAIN", "mkt")


def test_patch_resource_flags(client, db_session):
    ds = _make_datasource(db_session)
    sync_datasource(db_session, ds, FakeAdapter([_table("tmp_import")]))
    resource = db_session.query(ResourceTable).filter_by(table_name="tmp_import").one()
    assert resource.is_temp is True

    resp = client.patch(f"/api/v1/resources/{resource.id}", json={"is_temp": False, "is_system": True})
    assert resp.status_code == 200
    assert resp.json()["is_temp"] is False
    assert resp.json()["is_system"] is True


def test_domain_create_and_delete_guard(client, db_session):
    from app.models.asset import Asset
    from app.models.domain import Domain
    from app.models.resource_table import ResourceTable

    created = client.post(
        "/api/v1/domains",
        json={"domain_code": "fin", "domain_name": "财务", "description": "费用结算", "sort": 11},
    )
    assert created.status_code == 201
    assert created.json()["domain_code"] == "fin"

    # 重复域码
    assert (
        client.post("/api/v1/domains", json={"domain_code": "FIN", "domain_name": "财务2"}).status_code
        == 409
    )

    # 无资产时可删除
    assert client.delete(f"/api/v1/domains/{created.json()['id']}").status_code == 204

    # 有资产时禁止删除
    domain = Domain(domain_code="mkt", domain_name="客户与营销", sort=1)
    db_session.add(domain)
    db_session.commit()
    resource = ResourceTable(
        datasource_id=1, schema_name="cdm", table_name="dwd_mkt_billing", table_comment="计费"
    )
    db_session.add(resource)
    db_session.commit()
    db_session.add(Asset(resource_table_id=resource.id, asset_name="计费", domain_code="mkt", status="PUBLISHED"))
    db_session.commit()

    resp = client.delete(f"/api/v1/domains/{domain.id}")
    assert resp.status_code == 409
    assert "不能删除" in resp.json()["detail"]


def test_domain_patch(client, db_session):
    from app.models.domain import Domain

    db_session.add(Domain(domain_code="mkt", domain_name="客户与营销", sampled=True, sort=1))
    db_session.commit()
    domain = db_session.query(Domain).filter_by(domain_code="mkt").one()

    resp = client.patch(f"/api/v1/domains/{domain.id}", json={"description": "计费与资金流动"})
    assert resp.status_code == 200
    assert resp.json()["description"] == "计费与资金流动"


def asset_columns(db, asset_id):
    from app.models.asset_column import AssetColumn

    return db.query(AssetColumn).filter_by(asset_id=asset_id).all()


def test_sync_adds_columns_to_registered_asset(db_session):
    ds = _make_datasource(db_session)
    sync_datasource(db_session, ds, FakeAdapter([_table("dwd_mkt_billing")]))
    resource = db_session.query(ResourceTable).filter_by(table_name="dwd_mkt_billing").one()
    register_resources(db_session, ds.id, [RegisterItem(resource_id=resource.id)])

    extra = _table(
        "dwd_mkt_billing",
        columns=[
            RemoteColumn("id", 1, "bigint", False, None, "主键", True),
            RemoteColumn("ds", 2, "string", True, None, "分区", False),
            RemoteColumn("bill_amount", 3, "decimal", True, None, "账单金额", False),
        ],
    )
    sync_datasource(db_session, ds, FakeAdapter([extra]))

    asset = db_session.query(Asset).filter_by(resource_table_id=resource.id).one()
    names = {c.column_name for c in asset_columns(db_session, asset.id)}
    assert names == {"id", "ds", "bill_amount"}
