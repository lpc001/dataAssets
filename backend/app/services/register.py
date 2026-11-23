"""资产登记：从资源池挑选资源表，登记为资产（1 资产 = 1 张资源表）。"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.asset_column import AssetColumn
from app.models.resource_column import ResourceColumn
from app.models.resource_table import ResourceTable
from app.schemas.catalog import RegisterItem
from app.services.classify import owner_domain


def register_resources(
    db: Session,
    datasource_id: int,
    items: list[RegisterItem],
    operator: str | None = None,
) -> list[Asset]:
    """批量登记；已登记的资源跳过。items 里的名称/域/追溯档可覆盖规则建议值。"""
    if not items:
        return []
    ids = [i.resource_id for i in items]
    rows = db.scalars(
        select(ResourceTable).where(
            ResourceTable.id.in_(ids),
            ResourceTable.datasource_id == datasource_id,
        )
    ).all()
    resources = {r.id: r for r in rows}
    registered = set(
        db.scalars(select(Asset.resource_table_id).where(Asset.resource_table_id.in_(ids))).all()
    )

    created: list[Asset] = []
    now = datetime.now()
    for item in items:
        resource = resources.get(item.resource_id)
        if resource is None or resource.id in registered:
            continue
        domain = item.domain_code if item.domain_code is not None else resource.suggested_domain
        asset = Asset(
            resource_table_id=resource.id,
            asset_name=item.asset_name or resource.table_comment or resource.table_name,
            domain_code=domain,
            owner_domain_code=owner_domain(resource.table_name, domain),
            trace_level=item.trace_level if item.trace_level is not None else resource.suggested_trace,
            status="PUBLISHED",
            owner_name=item.owner_name or operator,
            created_at=now,
            updated_at=now,
        )
        db.add(asset)
        db.flush()
        asset.asset_code = f"DA{asset.id:05d}"

        columns = db.scalars(
            select(ResourceColumn)
            .where(ResourceColumn.resource_table_id == resource.id)
            .order_by(ResourceColumn.ordinal)
        ).all()
        for col in columns:
            db.add(
                AssetColumn(
                    asset_id=asset.id,
                    resource_column_id=col.id,
                    column_name=col.column_name,
                    ordinal=col.ordinal,
                    business_name=col.column_comment,
                    sensitive_level="L1",
                    is_key=col.is_primary_key,
                )
            )
        created.append(asset)

    db.commit()
    for asset in created:
        db.refresh(asset)
    return created
