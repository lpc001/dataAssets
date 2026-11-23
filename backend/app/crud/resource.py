from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.resource_column import ResourceColumn
from app.models.resource_table import ResourceTable


def list_resources(
    db: Session,
    datasource_id: int | None = None,
    schema_name: str | None = None,
    kind: str | None = None,
    registered: bool | None = None,
    keyword: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[ResourceTable], int]:
    stmt = select(ResourceTable)
    if datasource_id:
        stmt = stmt.where(ResourceTable.datasource_id == datasource_id)
    if schema_name:
        stmt = stmt.where(ResourceTable.schema_name == schema_name)
    if kind:
        stmt = stmt.where(ResourceTable.table_kind == kind)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(ResourceTable.table_name.ilike(like), ResourceTable.table_comment.ilike(like))
        )
    if registered is not None:
        registered_ids = select(Asset.resource_table_id)
        stmt = stmt.where(
            ResourceTable.id.in_(registered_ids)
            if registered
            else ResourceTable.id.not_in(registered_ids)
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(ResourceTable.schema_name, ResourceTable.table_name).offset(offset).limit(limit)
    ).all()
    return list(rows), int(total)


def get(db: Session, resource_id: int) -> ResourceTable | None:
    return db.get(ResourceTable, resource_id)


def columns(db: Session, resource_id: int) -> list[ResourceColumn]:
    return list(
        db.scalars(
            select(ResourceColumn)
            .where(ResourceColumn.resource_table_id == resource_id)
            .order_by(ResourceColumn.ordinal)
        ).all()
    )


def registered_ids(db: Session, resource_ids: list[int]) -> set[int]:
    if not resource_ids:
        return set()
    return set(
        db.scalars(select(Asset.resource_table_id).where(Asset.resource_table_id.in_(resource_ids))).all()
    )


def asset_map(db: Session, resource_ids: list[int]) -> dict[int, int]:
    """资源表 ID → 资产 ID（仅已登记的）。"""
    if not resource_ids:
        return {}
    rows = db.execute(
        select(Asset.resource_table_id, Asset.id).where(Asset.resource_table_id.in_(resource_ids))
    ).all()
    return {r[0]: r[1] for r in rows}


def summary(db: Session) -> dict:
    from app.models.datasource import DataSource
    from app.models.domain import Domain

    return {
        "datasource_count": db.scalar(select(func.count()).select_from(DataSource)) or 0,
        "resource_count": db.scalar(select(func.count()).select_from(ResourceTable)) or 0,
        "asset_count": db.scalar(select(func.count()).select_from(Asset)) or 0,
        "column_count": db.scalar(select(func.count()).select_from(ResourceColumn)) or 0,
        "domain_count": db.scalar(select(func.count()).select_from(Domain)) or 0,
        "missing_count": db.scalar(
            select(func.count()).select_from(ResourceTable).where(ResourceTable.remote_status == "MISSING")
        ) or 0,
    }
