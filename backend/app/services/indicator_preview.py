"""指标聚合预览：按维度分组统计度量，支持关联资产（LEFT/INNER JOIN）。"""

import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import create_engine, text

from app.adapters.postgres import build_url
from app.core.crypto import decrypt_text
from app.models.datasource import DataSource

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
AGG_FUNCS = {"SUM": "sum", "AVG": "avg", "COUNT": "count", "MAX": "max", "MIN": "min"}
GRAIN_UNITS = {"YEAR": "year", "QUARTER": "quarter", "MONTH": "month", "DAY": "day"}


def _ident(value: str) -> str:
    if not _IDENT_RE.match(value or ""):
        raise ValueError(f"非法标识符：{value}")
    return f'"{value}"'


def aggregate_preview(
    datasource: DataSource,
    main_schema: str,
    main_table: str,
    measure_column: str | None,
    aggregation: str,
    dimensions: list[dict],
    joins: list[dict] | None = None,
    limit: int = 20,
) -> tuple[list[str], list[list]]:
    if aggregation not in AGG_FUNCS:
        raise ValueError("不支持的聚合方式")

    selects: list[str] = []
    group_by: list[str] = []
    for index, dim in enumerate(dimensions, start=1):
        ref = f"{dim['alias']}.{_ident(dim['column'])}"
        alias = _ident(dim.get("name") or dim["column"])
        grain = dim.get("time_grain")
        if grain:
            unit = GRAIN_UNITS.get(grain)
            if not unit:
                raise ValueError("不支持的时间粒度")
            selects.append(f"date_trunc('{unit}', {ref})::date as {alias}")
        else:
            selects.append(f"{ref} as {alias}")
        group_by.append(str(index))

    if measure_column:
        expr = f"{AGG_FUNCS[aggregation]}(t0.{_ident(measure_column)})"
    else:
        expr = "count(t0.*)"
    selects.append(f"{expr} as {_ident('value')}")

    join_sql = ""
    for join in joins or []:
        alias = join["alias"]
        if alias == "t0":
            continue
        join_type = "left" if join.get("join_type", "LEFT").upper() == "LEFT" else "inner"
        join_sql += (
            f" {join_type} join {_ident(join['schema'])}.{_ident(join['table'])} {alias}"
            f" on t0.{_ident(join['left_column'])} = {alias}.{_ident(join['right_column'])}"
        )

    group_sql = f" group by {', '.join(group_by)}" if group_by else ""
    order_sql = f" order by {', '.join(group_by)}" if group_by else " order by 1"
    sql = (
        f"select {', '.join(selects)} from {_ident(main_schema)}.{_ident(main_table)} t0"
        f"{join_sql}{group_sql}{order_sql} limit :lim"
    )
    url = build_url(
        datasource.host, datasource.port, datasource.database_name,
        datasource.username, decrypt_text(datasource.password_cipher),
    )
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("set statement_timeout = '10000'"))
            result = conn.execute(text(sql), {"lim": max(1, min(int(limit), 100))})
            columns = list(result.keys())
            rows = [[_json(v) for v in row] for row in result.fetchall()]
        return columns, rows
    finally:
        engine.dispose()


def _json(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    return value
