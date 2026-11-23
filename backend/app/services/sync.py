"""元数据同步：把目标库结构写入资源池，并生成一次版本记录与逐项变化明细。"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.base import MetadataAdapter, RemoteColumn, RemoteTable
from app.models.asset import Asset
from app.models.asset_column import AssetColumn
from app.models.datasource import DataSource
from app.models.meta_change import MetaChange
from app.models.meta_version import MetaVersion
from app.models.resource_column import ResourceColumn
from app.models.resource_table import ResourceTable
from app.services.classify import (
    classify_table,
    detect_system,
    detect_temp,
    table_kind,
)


def parse_schemas(value: str) -> list[str]:
    return [s.strip() for s in (value or "").split(",") if s.strip()]


def _change(
    version_id: int,
    object_type: str,
    schema: str,
    table: str,
    change_type: str,
    column: str | None = None,
    field: str | None = None,
    old=None,
    new=None,
) -> MetaChange:
    return MetaChange(
        version_id=version_id,
        object_type=object_type,
        schema_name=schema,
        table_name=table,
        column_name=column,
        change_type=change_type,
        field_name=field,
        old_value=None if old is None else str(old)[:2000],
        new_value=None if new is None else str(new)[:2000],
    )


def _sync_columns(
    db: Session,
    table: ResourceTable,
    remote: list[RemoteColumn],
    version: MetaVersion,
    changes: list[MetaChange],
) -> bool:
    existing = {
        c.column_name: c
        for c in db.scalars(
            select(ResourceColumn).where(ResourceColumn.resource_table_id == table.id)
        ).all()
    }
    remote_names = {c.name for c in remote}
    changed = False
    asset = db.scalars(select(Asset).where(Asset.resource_table_id == table.id)).first()

    for rc in remote:
        current = existing.get(rc.name)
        if current is None:
            col = ResourceColumn(
                resource_table_id=table.id,
                column_name=rc.name,
                ordinal=rc.ordinal,
                data_type=rc.data_type,
                is_nullable=rc.nullable,
                column_default=rc.default,
                is_primary_key=rc.is_primary_key,
                column_comment=rc.comment,
                is_partition_key=(rc.name.lower() == "ds"),
            )
            db.add(col)
            db.flush()
            changes.append(
                _change(version.id, "COLUMN", table.schema_name, table.table_name, "ADD", rc.name)
            )
            version.column_added += 1
            changed = True
            if asset is not None:
                db.add(
                    AssetColumn(
                        asset_id=asset.id,
                        resource_column_id=col.id,
                        column_name=rc.name,
                        ordinal=rc.ordinal,
                        business_name=rc.comment,
                        sensitive_level="L1",
                        is_key=rc.is_primary_key,
                    )
                )
            continue

        field_changes = [
            ("data_type", current.data_type, rc.data_type),
            ("is_nullable", current.is_nullable, rc.nullable),
            ("column_default", current.column_default, rc.default),
            ("is_primary_key", current.is_primary_key, rc.is_primary_key),
            ("column_comment", current.column_comment, rc.comment),
        ]
        hit = False
        for name, old, new in field_changes:
            if old != new:
                changes.append(
                    _change(
                        version.id, "COLUMN", table.schema_name, table.table_name, "MODIFY", rc.name, name, old, new
                    )
                )
                hit = True
        if hit:
            version.column_changed += 1
            changed = True
        current.data_type = rc.data_type
        current.is_nullable = rc.nullable
        current.column_default = rc.default
        current.is_primary_key = rc.is_primary_key
        current.column_comment = rc.comment
        current.ordinal = rc.ordinal
        if current.remote_status != "ACTIVE":
            current.remote_status = "ACTIVE"
            changed = True

    for name, current in existing.items():
        if name not in remote_names and current.remote_status != "MISSING":
            current.remote_status = "MISSING"
            changes.append(
                _change(version.id, "COLUMN", table.schema_name, table.table_name, "DROP", name)
            )
            version.column_dropped += 1
            changed = True
    return changed


def _upsert_table(
    db: Session,
    datasource_id: int,
    rt: RemoteTable,
    relkind: str | None,
    now: datetime,
    version: MetaVersion,
    changes: list[MetaChange],
    existing: dict[tuple[str, str], ResourceTable],
) -> None:
    key = (rt.schema, rt.name)
    row = existing.get(key)
    layer, domain, trace = classify_table(rt.name)

    if row is None:
        row = ResourceTable(
            datasource_id=datasource_id,
            schema_name=rt.schema,
            table_name=rt.name,
            table_comment=rt.comment,
            table_kind=table_kind(relkind),
            is_system=detect_system(rt.schema, rt.name),
            is_temp=detect_temp(rt.name),
            row_count=rt.row_count,
            column_count=len(rt.columns),
            suggested_layer=layer,
            suggested_domain=domain,
            suggested_trace=trace,
            first_seen_at=now,
            last_seen_at=now,
        )
        db.add(row)
        db.flush()
        existing[key] = row
        changes.append(_change(version.id, "TABLE", rt.schema, rt.name, "ADD"))
        version.table_added += 1
        _sync_columns(db, row, rt.columns, version, changes)
        return

    changed = False
    if row.table_comment != rt.comment:
        changes.append(
            _change(version.id, "TABLE", rt.schema, rt.name, "MODIFY", field="table_comment", old=row.table_comment, new=rt.comment)
        )
        row.table_comment = rt.comment
        changed = True
    if row.remote_status != "ACTIVE":
        row.remote_status = "ACTIVE"
        changed = True
    row.row_count = rt.row_count
    row.column_count = len(rt.columns)
    row.last_seen_at = now
    if _sync_columns(db, row, rt.columns, version, changes):
        changed = True
    if changed:
        version.table_changed += 1


def sync_datasource(
    db: Session,
    datasource: DataSource,
    adapter: MetadataAdapter,
    operator: str | None = None,
) -> MetaVersion:
    """执行一次采集：写入资源池，产生一个新版本与变化明细。"""
    last_no = db.scalar(
        select(func.max(MetaVersion.version_no)).where(MetaVersion.datasource_id == datasource.id)
    ) or 0
    version = MetaVersion(
        datasource_id=datasource.id,
        version_no=int(last_no) + 1,
        started_at=datetime.now(),
        status="RUNNING",
        operator=operator,
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    try:
        now = datetime.now()
        schemas = parse_schemas(datasource.schema_filter)
        remote_tables = adapter.fetch_tables(schemas)
        existing = {
            (r.schema_name, r.table_name): r
            for r in db.scalars(
                select(ResourceTable).where(ResourceTable.datasource_id == datasource.id)
            ).all()
        }
        changes: list[MetaChange] = []

        for rt in remote_tables:
            _upsert_table(db, datasource.id, rt, None, now, version, changes, existing)

        remote_keys = {(rt.schema, rt.name) for rt in remote_tables}
        for key, row in existing.items():
            if key not in remote_keys and row.remote_status != "MISSING":
                row.remote_status = "MISSING"
                changes.append(_change(version.id, "TABLE", row.schema_name, row.table_name, "DROP"))
                version.table_dropped += 1

        for change in changes:
            db.add(change)

        datasource.last_sync_at = now
        version.status = "SUCCESS"
        version.finished_at = datetime.now()
        version.message = (
            f"表 新增{version.table_added}/变更{version.table_changed}/消失{version.table_dropped}；"
            f"字段 新增{version.column_added}/变更{version.column_changed}/消失{version.column_dropped}"
        )
        db.commit()
        db.refresh(version)
        return version
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        failed = MetaVersion(
            datasource_id=datasource.id,
            version_no=int(last_no) + 1,
            started_at=datetime.now(),
            finished_at=datetime.now(),
            status="FAILED",
            operator=operator,
            message=f"{exc.__class__.__name__}: {exc}",
        )
        db.add(failed)
        db.commit()
        db.refresh(failed)
        return failed
