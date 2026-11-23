# -*- coding: utf-8 -*-
"""一次性迁移：把单层 ast_table/ast_column 拆成 资源池 + 资产 两层。

可重复执行：仅当旧表存在且资产表为空时执行复制，最后删除旧表。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text  # noqa: E402

import app.models  # noqa: F401,E402  确保所有模型注册
from app.core.database import Base, engine  # noqa: E402

COPY_TABLES = text(
    """
    insert into ast_resource_table
        (datasource_id, schema_name, table_name, table_comment, table_kind,
         is_system, is_temp, row_count, column_count,
         suggested_layer, suggested_domain, suggested_trace,
         first_seen_at, last_seen_at, remote_status)
    select datasource_id, schema_name, table_name, table_comment, 'TABLE',
           false, false, row_count, 0,
           layer, domain_code, trace_level,
           now(), now(), remote_status
      from ast_table
    """
)

COPY_COLUMNS = text(
    """
    insert into ast_resource_column
        (resource_table_id, column_name, ordinal, data_type, is_nullable, column_default,
         is_primary_key, column_comment, is_partition_key, remote_status)
    select rt.id, c.column_name, c.ordinal, c.data_type, c.is_nullable, c.column_default,
           c.is_primary_key, c.column_comment, c.is_partition_key, c.remote_status
      from ast_column c
      join ast_table t on t.id = c.table_id
      join ast_resource_table rt
        on rt.datasource_id = t.datasource_id
       and rt.schema_name = t.schema_name
       and rt.table_name = t.table_name
    """
)

COPY_ASSETS = text(
    """
    insert into ast_asset
        (resource_table_id, asset_name, domain_code, owner_domain_code, trace_level,
         status, owner_name, created_at, updated_at)
    select rt.id,
           coalesce(nullif(t.business_name, ''), nullif(t.table_comment, ''), rt.table_name),
           t.domain_code, t.owner_domain_code, t.trace_level,
           'PUBLISHED', 'admin', now(), now()
      from ast_table t
      join ast_resource_table rt
        on rt.datasource_id = t.datasource_id
       and rt.schema_name = t.schema_name
       and rt.table_name = t.table_name
    """
)

FILL_CODES = text("update ast_asset set asset_code = 'DA' || lpad(cast(id as text), 5, '0') where asset_code is null")

COPY_ASSET_COLUMNS = text(
    """
    insert into ast_asset_column
        (asset_id, resource_column_id, column_name, ordinal, business_name, sensitive_level, is_key)
    select a.id, rc.id, rc.column_name, rc.ordinal,
           coalesce(nullif(c.business_name, ''), rc.column_comment),
           c.sensitive_level, rc.is_primary_key
      from ast_asset a
      join ast_table t on t.id = (
            select t2.id from ast_table t2
             join ast_resource_table rt2 on rt2.id = a.resource_table_id
             where t2.datasource_id = rt2.datasource_id
               and t2.schema_name = rt2.schema_name
               and t2.table_name = rt2.table_name
             limit 1)
      join ast_column c on c.table_id = t.id
      join ast_resource_column rc
        on rc.resource_table_id = a.resource_table_id
       and rc.column_name = c.column_name
    """
)

UPDATE_COLUMN_COUNT = text(
    "update ast_resource_table rt set column_count = "
    "(select count(*) from ast_resource_column c where c.resource_table_id = rt.id)"
)

DROP_OLD = [
    "drop table if exists ast_column",
    "drop table if exists ast_table",
    "drop table if exists ast_sync_log",
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        has_old = conn.execute(text("select to_regclass('public.ast_table')")).scalar()
        asset_count = conn.execute(text("select count(*) from ast_asset")).scalar() or 0

        if has_old and asset_count == 0:
            conn.execute(COPY_TABLES)
            conn.execute(COPY_COLUMNS)
            conn.execute(COPY_ASSETS)
            conn.execute(FILL_CODES)
            conn.execute(COPY_ASSET_COLUMNS)
            conn.execute(UPDATE_COLUMN_COUNT)
            print("已迁移：资源表 / 资源字段 / 资产 / 资产字段")
        elif has_old:
            print("资产表已有数据，跳过复制，仅清理旧表")

        for stmt in DROP_OLD:
            conn.execute(text(stmt))

        counts = {
            "resource_table": conn.execute(text("select count(*) from ast_resource_table")).scalar(),
            "resource_column": conn.execute(text("select count(*) from ast_resource_column")).scalar(),
            "asset": conn.execute(text("select count(*) from ast_asset")).scalar(),
            "asset_column": conn.execute(text("select count(*) from ast_asset_column")).scalar(),
        }
    print("双层模型迁移完成：", counts)


if __name__ == "__main__":
    main()
