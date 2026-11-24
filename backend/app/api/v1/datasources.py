from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.adapters.postgres import PostgresAdapter, build_url
from app.api.deps import get_current_user
from app.core.crypto import decrypt_text
from app.core.database import get_db
from app.crud import datasource as crud
from app.models.asset import Asset
from app.models.datasource import DataSource
from app.models.meta_change import MetaChange
from app.models.meta_version import MetaVersion
from app.models.resource_column import ResourceColumn
from app.models.resource_table import ResourceTable
from app.models.user import User
from app.schemas.datasource import (
    ConnectionTestResult,
    SchemaListOut,
    SchemaQueryIn,
    DataSourceCreate,
    DataSourceOut,
    DataSourceUpdate,
    MetaChangeOut,
    MetaVersionOut,
)
from app.services.permissions import require_perm
from app.services.sync import sync_datasource

router = APIRouter(prefix="/datasources", tags=["数据源管理"])


def _url(ds: DataSource) -> str:
    password = quote_plus(decrypt_text(ds.password_cipher))
    return f"postgresql+psycopg2://{ds.username}:{password}@{ds.host}:{ds.port}/{ds.database_name}"


def _adapter(ds: DataSource) -> PostgresAdapter:
    return PostgresAdapter(_url(ds))


@router.get("", response_model=list[DataSourceOut])
def list_datasources(
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:datasource")),
):
    return crud.list_all(db)


@router.post("", response_model=DataSourceOut, status_code=201)
def create_datasource(
    payload: DataSourceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:datasource")),
):
    if crud.get_by_name(db, payload.name):
        raise HTTPException(status_code=409, detail="数据源名称已存在")
    row = crud.create(db, payload)
    adapter = _adapter(row)
    try:
        ok, _ = adapter.test_connection()
        if ok:
            row.readonly_verified = adapter.is_readonly()
    finally:
        adapter.dispose()
    db.commit()
    db.refresh(row)
    return row


@router.put("/{datasource_id}", response_model=DataSourceOut)
def update_datasource(
    datasource_id: int,
    payload: DataSourceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:datasource")),
):
    row = crud.get(db, datasource_id)
    if row is None:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return crud.update(db, row, payload)


@router.delete("/{datasource_id}", status_code=204)
def delete_datasource(
    datasource_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:datasource")),
):
    row = crud.get(db, datasource_id)
    if row is None:
        raise HTTPException(status_code=404, detail="数据源不存在")
    resource_ids = [
        r.id for r in db.scalars(select(ResourceTable).where(ResourceTable.datasource_id == row.id)).all()
    ]
    if resource_ids:
        asset_ids = [
            a.id for a in db.scalars(select(Asset).where(Asset.resource_table_id.in_(resource_ids))).all()
        ]
        if asset_ids:
            from app.models.asset_column import AssetColumn

            db.execute(delete(AssetColumn).where(AssetColumn.asset_id.in_(asset_ids)))
            db.execute(delete(Asset).where(Asset.id.in_(asset_ids)))
        db.execute(delete(ResourceColumn).where(ResourceColumn.resource_table_id.in_(resource_ids)))
        db.execute(delete(ResourceTable).where(ResourceTable.id.in_(resource_ids)))
    version_ids = [
        v.id for v in db.scalars(select(MetaVersion).where(MetaVersion.datasource_id == row.id)).all()
    ]
    if version_ids:
        db.execute(delete(MetaChange).where(MetaChange.version_id.in_(version_ids)))
        db.execute(delete(MetaVersion).where(MetaVersion.id.in_(version_ids)))
    db.delete(row)
    db.commit()


@router.post("/schemas", response_model=SchemaListOut)
def list_schemas(
    payload: SchemaQueryIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:datasource")),
):
    password = payload.password
    if not password and payload.datasource_id:
        row = crud.get(db, payload.datasource_id)
        password = decrypt_text(row.password_cipher) if row else ""
    if not password:
        raise HTTPException(status_code=400, detail="请先填写口令")
    url = build_url(payload.host, payload.port, payload.database_name, payload.username, password)
    adapter = PostgresAdapter(url)
    try:
        schemas = adapter.list_schemas()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"读取 Schema 失败：{exc.__class__.__name__}") from exc
    finally:
        adapter.dispose()
    return SchemaListOut(schemas=schemas)


@router.post("/{datasource_id}/test", response_model=ConnectionTestResult)
def test_datasource(
    datasource_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:datasource")),
):
    row = crud.get(db, datasource_id)
    if row is None:
        raise HTTPException(status_code=404, detail="数据源不存在")
    adapter = _adapter(row)
    try:
        ok, message = adapter.test_connection()
        readonly = adapter.is_readonly() if ok else False
    finally:
        adapter.dispose()
    row.readonly_verified = readonly
    db.commit()
    return ConnectionTestResult(ok=ok, readonly=readonly, message=message)


@router.post("/{datasource_id}/sync", response_model=MetaVersionOut)
def sync_now(
    datasource_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:datasource")),
):
    row = crud.get(db, datasource_id)
    if row is None:
        raise HTTPException(status_code=404, detail="数据源不存在")
    adapter = _adapter(row)
    try:
        version = sync_datasource(db, row, adapter, operator=user.username)
    finally:
        adapter.dispose()
    if version.status == "FAILED":
        raise HTTPException(status_code=502, detail=f"采集失败：{version.message}")
    return version


@router.get("/{datasource_id}/versions", response_model=list[MetaVersionOut])
def list_versions(
    datasource_id: int,
    limit: int = Query(30, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:datasource")),
):
    return crud.list_versions(db, datasource_id, limit)


@router.get("/versions/{version_id}/changes", response_model=list[MetaChangeOut])
def list_version_changes(
    version_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:datasource")),
):
    return list(
        db.scalars(
            select(MetaChange).where(MetaChange.version_id == version_id).order_by(MetaChange.id)
        ).all()
    )
