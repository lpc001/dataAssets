import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.crud import asset as asset_crud
from app.crud import resource as resource_crud
from app.models.domain import Domain
from app.models.resource_table import ResourceTable
from app.models.subject import Subject
from app.models.user import User
from sqlalchemy import func

from app.models.asset import Asset
from app.models.asset_column import AssetColumn
from app.models.datasource import DataSource
from app.schemas.catalog import (
    AssetColumnOut,
    DataMapOut,
    MapAsset,
    MapDomain,
    AssetColumnPatch,
    AssetDetail,
    AssetOut,
    AssetPage,
    AssetPatch,
    DomainCreate,
    DomainOut,
    DomainPatch,
    RegisterRequest,
    ResourceColumnOut,
    ResourceDetail,
    PreviewOut,
    ResourcePage,
    ResourcePatch,
    ResourceTableOut,
    SubjectOut,
    SummaryOut,
)
from app.services.permissions import require_perm
from app.services.preview import preview_rows


def _parse_columns(value: str | None) -> list[str] | None:
    if not value:
        return None
    items = [c.strip() for c in value.split(",") if c.strip()]
    return items or None
from app.services.register import register_resources

router = APIRouter(tags=["资产目录"])


def _asset_out(asset, resource) -> AssetOut:
    data = AssetOut.model_validate(asset)
    data.schema_name = resource.schema_name
    data.table_name = resource.table_name
    data.data_layer = resource.suggested_layer
    data.row_count = resource.row_count
    return data


@router.get("/domains", response_model=list[DomainOut])
def list_domains(
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    rows = list(db.scalars(select(Domain).order_by(Domain.sort)).all())
    counts = dict(
        db.execute(select(Asset.domain_code, func.count()).group_by(Asset.domain_code)).all()
    )
    result = []
    for row in rows:
        out = DomainOut.model_validate(row)
        out.asset_count = int(counts.get(row.domain_code, 0))
        result.append(out)
    return result


@router.post("/domains", response_model=DomainOut, status_code=201)
def create_domain(
    payload: DomainCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    code = payload.domain_code.strip().lower()
    if not re.fullmatch(r"[a-z]{3,8}", code):
        raise HTTPException(status_code=422, detail="域码只能由 3-8 位小写字母组成")
    if db.scalars(select(Domain).where(Domain.domain_code == code)).first():
        raise HTTPException(status_code=409, detail="域码已存在")
    row = Domain(
        domain_code=code,
        domain_name=payload.domain_name,
        description=payload.description,
        sort=payload.sort,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return DomainOut.model_validate(row)


@router.delete("/domains/{domain_id}", status_code=204)
def delete_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    row = db.get(Domain, domain_id)
    if row is None:
        raise HTTPException(status_code=404, detail="数据域不存在")
    used = db.scalar(
        select(func.count()).select_from(Asset).where(Asset.domain_code == row.domain_code)
    )
    if used:
        raise HTTPException(
            status_code=409,
            detail=f"该域下已有 {used} 个已登记资产，不能删除；请先调整或下线这些资产的数据域",
        )
    db.delete(row)
    db.commit()


@router.patch("/domains/{domain_id}", response_model=DomainOut)
def patch_domain(
    domain_id: int,
    payload: DomainPatch,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    row = db.get(Domain, domain_id)
    if row is None:
        raise HTTPException(status_code=404, detail="数据域不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return DomainOut.model_validate(row)


@router.get("/subjects", response_model=list[SubjectOut])
def list_subjects(
    domain_code: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    stmt = select(Subject)
    if domain_code:
        stmt = stmt.where(Subject.domain_code == domain_code)
    return list(db.scalars(stmt.order_by(Subject.sort)).all())


# ---------------- 资源池 ----------------
@router.get("/resources", response_model=ResourcePage)
def list_resources(
    datasource_id: int | None = None,
    schema_name: str | None = None,
    kind: str | None = None,
    registered: bool | None = None,
    group_type: str | None = None,
    asset_status: str | None = None,
    is_system: bool | None = None,
    is_temp: bool | None = None,
    keyword: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    rows, total = resource_crud.list_resources(
        db,
        datasource_id=datasource_id,
        schema_name=schema_name,
        kind=kind,
        registered=registered,
        group_type=group_type,
        asset_status=asset_status,
        is_system=is_system,
        is_temp=is_temp,
        keyword=keyword,
        offset=(page - 1) * page_size,
        limit=page_size,
    )
    assets = resource_crud.asset_map(db, [r.id for r in rows])
    items = []
    for r in rows:
        out = ResourceTableOut.model_validate(r)
        hit = assets.get(r.id)
        out.registered = hit is not None
        out.asset_id = hit[0] if hit else None
        out.asset_status = hit[1] if hit else None
        items.append(out)
    return ResourcePage(items=items, total=total)


@router.get("/resources/{resource_id}/preview", response_model=PreviewOut)
def preview_resource(
    resource_id: int,
    limit: int = Query(20, ge=1, le=100),
    columns: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:preview")),
):
    row = resource_crud.get(db, resource_id)
    if row is None:
        raise HTTPException(status_code=404, detail="资源不存在")
    datasource = db.get(DataSource, row.datasource_id)
    if datasource is None:
        raise HTTPException(status_code=404, detail="数据源不存在")
    all_columns = [c.column_name for c in resource_crud.columns(db, row.id)]
    picked = _parse_columns(columns)
    if picked and any(c not in all_columns for c in picked):
        raise HTTPException(status_code=400, detail="包含不存在的字段")
    try:
        cols, rows, masked = preview_rows(
            db,
            datasource,
            row,
            limit=limit,
            columns=picked,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"预览失败：{exc.__class__.__name__}") from exc
    return PreviewOut(
        columns=cols,
        rows=rows,
        limit=limit,
        schema_name=row.schema_name,
        table_name=row.table_name,
        masked_columns=masked,
        all_columns=all_columns,
    )


@router.patch("/resources/{resource_id}", response_model=ResourceTableOut)
def patch_resource(
    resource_id: int,
    payload: ResourcePatch,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    row = resource_crud.get(db, resource_id)
    if row is None:
        raise HTTPException(status_code=404, detail="资源不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return ResourceTableOut.model_validate(row)


@router.get("/resources/{resource_id}", response_model=ResourceDetail)
def get_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    row = resource_crud.get(db, resource_id)
    if row is None:
        raise HTTPException(status_code=404, detail="资源不存在")
    detail = ResourceDetail.model_validate(row)
    assets = resource_crud.asset_map(db, [row.id])
    hit = assets.get(row.id)
    detail.registered = hit is not None
    detail.asset_id = hit[0] if hit else None
    detail.asset_status = hit[1] if hit else None
    detail.columns = [ResourceColumnOut.model_validate(c) for c in resource_crud.columns(db, row.id)]
    return detail


# ---------------- 资产 ----------------
@router.get("/assets", response_model=AssetPage)
def list_assets(
    domain_code: str | None = None,
    public_only: bool = False,
    group_type: str | None = None,
    layer: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    rows, total = asset_crud.list_assets(
        db,
        domain_code=domain_code,
        group_type=group_type or ("PUBLIC" if public_only else None),
        layer=layer,
        status=status,
        keyword=keyword,
        offset=(page - 1) * page_size,
        limit=page_size,
    )
    return AssetPage(items=[_asset_out(a, r) for a, r in rows], total=total)


@router.get("/assets/{asset_id}", response_model=AssetDetail)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    asset = asset_crud.get(db, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="资产不存在")
    resource = asset_crud.resource_of(db, asset)
    if resource is None:
        raise HTTPException(status_code=404, detail="资产来源资源表不存在")
    detail = AssetDetail.model_validate(_asset_out(asset, resource))
    detail.columns = [AssetColumnOut(**c) for c in asset_crud.columns_with_type(db, asset.id)]
    return detail


@router.get("/assets/{asset_id}/preview", response_model=PreviewOut)
def preview_asset(
    asset_id: int,
    limit: int = Query(20, ge=1, le=100),
    columns: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:preview")),
):
    asset = asset_crud.get(db, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="资产不存在")
    resource = asset_crud.resource_of(db, asset)
    if resource is None:
        raise HTTPException(status_code=404, detail="来源资源表不存在")
    datasource = db.get(DataSource, resource.datasource_id)
    if datasource is None:
        raise HTTPException(status_code=404, detail="数据源不存在")

    asset_columns = asset_crud.columns_with_type(db, asset.id)
    all_columns = [c["column_name"] for c in asset_columns]
    sensitive = {c["column_name"]: c["sensitive_level"] for c in asset_columns}
    picked = _parse_columns(columns)
    if picked and any(c not in all_columns for c in picked):
        raise HTTPException(status_code=400, detail="包含不存在的字段")
    try:
        cols, rows, masked = preview_rows(
            db,
            datasource,
            resource,
            limit=limit,
            columns=picked,
            sensitive=sensitive,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"预览失败：{exc.__class__.__name__}") from exc
    return PreviewOut(
        columns=cols,
        rows=rows,
        limit=limit,
        schema_name=resource.schema_name,
        table_name=resource.table_name,
        masked_columns=masked,
        all_columns=all_columns,
    )


@router.patch("/assets/{asset_id}", response_model=AssetOut)
def patch_asset(
    asset_id: int,
    payload: AssetPatch,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    asset = asset_crud.get(db, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="资产不存在")
    asset = asset_crud.patch(db, asset, payload)
    resource = asset_crud.resource_of(db, asset)
    return _asset_out(asset, resource)


@router.patch("/asset-columns/{column_id}", response_model=AssetColumnOut)
def patch_asset_column(
    column_id: int,
    payload: AssetColumnPatch,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    column = asset_crud.get_column(db, column_id)
    if column is None:
        raise HTTPException(status_code=404, detail="资产字段不存在")
    column = asset_crud.patch_column(db, column, payload)
    rows = [c for c in asset_crud.columns_with_type(db, column.asset_id) if c["id"] == column.id]
    return AssetColumnOut(**rows[0]) if rows else AssetColumnOut.model_validate(column)


@router.post("/assets/register", response_model=list[AssetOut])
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    created = register_resources(db, payload.datasource_id, payload.items, operator=user.username)
    result = []
    for asset in created:
        resource = asset_crud.resource_of(db, asset)
        if resource is not None:
            result.append(_asset_out(asset, resource))
    return result


@router.get("/data-map", response_model=DataMapOut)
def data_map(
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    domain_rows = list(db.scalars(select(Domain).order_by(Domain.sort)).all())
    rows = db.execute(
        select(Asset, ResourceTable)
        .join(ResourceTable, ResourceTable.id == Asset.resource_table_id)
    ).all()
    column_counts = dict(
        db.execute(
            select(AssetColumn.asset_id, func.count()).group_by(AssetColumn.asset_id)
        ).all()
    )

    assets = []
    domain_agg: dict[str, dict] = {}
    for asset, resource in rows:
        cols = int(column_counts.get(asset.id, 0))
        assets.append(
            MapAsset(
                id=asset.id,
                asset_code=asset.asset_code,
                asset_name=asset.asset_name,
                table_name=resource.table_name,
                domain_code=asset.domain_code,
                group_type=asset.group_type,
                layer=resource.suggested_layer,
                rows=resource.row_count,
                columns=cols,
                status=asset.status,
            )
        )
        if asset.domain_code:
            agg = domain_agg.setdefault(
                asset.domain_code, {"asset_count": 0, "column_count": 0, "row_sum": 0}
            )
            agg["asset_count"] += 1
            agg["column_count"] += cols
            agg["row_sum"] += resource.row_count or 0

    domains = []
    for domain in domain_rows:
        agg = domain_agg.get(domain.domain_code, {"asset_count": 0, "column_count": 0, "row_sum": 0})
        domains.append(
            MapDomain(
                domain_code=domain.domain_code,
                domain_name=domain.domain_name,
                asset_count=agg["asset_count"],
                column_count=agg["column_count"],
                row_sum=agg["row_sum"],
                anchor_x=domain.anchor_x,
                anchor_y=domain.anchor_y,
            )
        )

    return DataMapOut(
        domain_count=len(domain_rows),
        asset_count=len(assets),
        column_count=sum(column_counts.values()),
        published_count=sum(1 for a in assets if a.status == "PUBLISHED"),
        domains=domains,
        assets=assets,
    )


@router.get("/asset-summary", response_model=SummaryOut)
def asset_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    return SummaryOut(**resource_crud.summary(db))
