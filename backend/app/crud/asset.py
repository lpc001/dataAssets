from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.asset_column import AssetColumn
from app.models.resource_column import ResourceColumn
from app.models.resource_table import ResourceTable
from app.schemas.catalog import AssetPatch


def list_assets(
    db: Session,
    domain_code: str | None = None,
    public_only: bool = False,
    layer: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[tuple[Asset, ResourceTable]], int]:
    stmt = select(Asset, ResourceTable).join(ResourceTable, ResourceTable.id == Asset.resource_table_id)
    if domain_code:
        stmt = stmt.where(Asset.domain_code == domain_code)
    if public_only:
        stmt = stmt.where(Asset.domain_code.is_(None))
    if layer:
        stmt = stmt.where(ResourceTable.suggested_layer == layer)
    if status:
        stmt = stmt.where(Asset.status == status)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Asset.asset_name.ilike(like),
                Asset.asset_code.ilike(like),
                ResourceTable.table_name.ilike(like),
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(
        stmt.order_by(ResourceTable.schema_name, ResourceTable.table_name).offset(offset).limit(limit)
    ).all()
    return [(r[0], r[1]) for r in rows], int(total)


def get(db: Session, asset_id: int) -> Asset | None:
    return db.get(Asset, asset_id)


def resource_of(db: Session, asset: Asset) -> ResourceTable | None:
    return db.get(ResourceTable, asset.resource_table_id)


def columns_with_type(db: Session, asset_id: int) -> list[dict]:
    rows = db.execute(
        select(AssetColumn, ResourceColumn)
        .join(ResourceColumn, ResourceColumn.id == AssetColumn.resource_column_id)
        .where(AssetColumn.asset_id == asset_id)
        .order_by(AssetColumn.ordinal)
    ).all()
    return [
        {
            "id": ac.id,
            "asset_id": ac.asset_id,
            "column_name": ac.column_name,
            "ordinal": ac.ordinal,
            "business_name": ac.business_name,
            "business_meaning": ac.business_meaning,
            "sensitive_level": ac.sensitive_level,
            "is_key": ac.is_key,
            "data_type": rc.data_type,
            "column_comment": rc.column_comment,
        }
        for ac, rc in rows
    ]


def get_column(db: Session, column_id: int) -> AssetColumn | None:
    return db.get(AssetColumn, column_id)


def patch(db: Session, asset: Asset, payload: AssetPatch) -> Asset:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, key, value)
    db.commit()
    db.refresh(asset)
    return asset


def patch_column(db: Session, column: AssetColumn, payload) -> AssetColumn:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(column, key, value)
    db.commit()
    db.refresh(column)
    return column
