import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.crud import asset as asset_crud
from app.crud import resource as resource_crud
from app.models.domain import Domain
from app.models.subject import Subject
from app.models.user import User
from sqlalchemy import func

from app.models.asset import Asset
from app.schemas.catalog import (
    AssetColumnOut,
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
    ResourcePage,
    ResourceTableOut,
    SubjectOut,
    SummaryOut,
)
from app.services.permissions import require_perm
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
        keyword=keyword,
        offset=(page - 1) * page_size,
        limit=page_size,
    )
    assets = resource_crud.asset_map(db, [r.id for r in rows])
    items = []
    for r in rows:
        out = ResourceTableOut.model_validate(r)
        out.registered = r.id in assets
        out.asset_id = assets.get(r.id)
        items.append(out)
    return ResourcePage(items=items, total=total)


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
    detail.registered = bool(assets)
    detail.asset_id = assets.get(row.id)
    detail.columns = [ResourceColumnOut.model_validate(c) for c in resource_crud.columns(db, row.id)]
    return detail


# ---------------- 资产 ----------------
@router.get("/assets", response_model=AssetPage)
def list_assets(
    domain_code: str | None = None,
    public_only: bool = False,
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
        public_only=public_only,
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


@router.get("/asset-summary", response_model=SummaryOut)
def asset_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:catalog")),
):
    return SummaryOut(**resource_crud.summary(db))
