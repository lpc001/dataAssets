"""PostgreSQL 元数据适配器。"""

import re
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

from app.adapters.base import MetadataAdapter, RemoteColumn, RemoteTable

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def build_url(host: str, port: int, database: str, username: str, password: str) -> str:
    return (
        f"postgresql+psycopg2://{username}:{quote_plus(password)}"
        f"@{host}:{port}/{database}"
    )


def _json_value(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    if isinstance(value, bytes):
        return f"<binary {len(value)} bytes>"
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


class PostgresAdapter(MetadataAdapter):
    def __init__(self, url: str) -> None:
        self._engine = create_engine(url, pool_pre_ping=True)

    def dispose(self) -> None:
        self._engine.dispose()

    def test_connection(self) -> tuple[bool, str]:
        try:
            with self._engine.connect() as conn:
                conn.execute(text("select 1"))
            return True, "连接成功"
        except Exception as exc:  # noqa: BLE001
            return False, f"连接失败：{exc.__class__.__name__}: {exc}"

    def is_readonly(self) -> bool:
        try:
            with self._engine.connect() as conn:
                row = conn.execute(
                    text("select rolsuper from pg_roles where rolname = current_user")
                ).fetchone()
            return bool(row) and not bool(row[0])
        except Exception:  # noqa: BLE001
            return False

    def _exact_count(self, conn, schema: str, table: str) -> int | None:
        """逐表精确计数；标识符先做白名单校验，避免注入。"""
        if not _IDENT_RE.match(schema) or not _IDENT_RE.match(table):
            return None
        try:
            value = conn.execute(
                text(f'select count(*) from "{schema}"."{table}"')
            ).scalar()
            return int(value or 0)
        except Exception:  # noqa: BLE001
            return None

    def fetch_sample(
        self, schema: str, table: str, limit: int = 20, columns: list[str] | None = None
    ) -> tuple[list[str], list[list]]:
        """只读抽样：强制限行 + 10 秒超时，标识符走白名单校验。"""
        if not _IDENT_RE.match(schema) or not _IDENT_RE.match(table):
            raise ValueError("非法标识符")
        limit = max(1, min(int(limit), 100))
        if columns:
            for col in columns:
                if not _IDENT_RE.match(col):
                    raise ValueError("非法字段名")
            projection = ", ".join(f'"{c}"' for c in columns)
        else:
            projection = "*"
        with self._engine.connect() as conn:
            conn.execute(text("set statement_timeout = '10000'"))
            result = conn.execute(
                text(f'select {projection} from "{schema}"."{table}" limit :lim'), {"lim": limit}
            )
            columns = list(result.keys())
            rows = [[_json_value(v) for v in row] for row in result.fetchall()]
        return columns, rows

    def fetch_tables(self, schemas: list[str]) -> list[RemoteTable]:
        if not schemas:
            return []
        names = ", ".join(f":s{i}" for i in range(len(schemas)))
        params = {f"s{i}": s for i, s in enumerate(schemas)}
        table_sql = text(
            f"""
            select n.nspname, c.relname,
                   obj_description(c.oid, 'pg_class') as tbl_comment,
                   coalesce(st.n_live_tup, 0) as est_rows
              from pg_class c
              join pg_namespace n on n.oid = c.relnamespace
              left join pg_stat_user_tables st on st.relid = c.oid
             where c.relkind = 'r'
               and n.nspname in ({names})
             order by n.nspname, c.relname
            """
        )
        column_sql = text(
            f"""
            select c.table_schema, c.table_name, c.column_name, c.ordinal_position,
                   c.data_type, c.is_nullable, c.column_default,
                   col_description(format('%I.%I', c.table_schema, c.table_name)::regclass::oid,
                                   c.ordinal_position) as col_comment
              from information_schema.columns c
             where c.table_schema in ({names})
             order by c.table_schema, c.table_name, c.ordinal_position
            """
        )
        pk_sql = text(
            f"""
            select kcu.table_schema, kcu.table_name, kcu.column_name
              from information_schema.table_constraints tc
              join information_schema.key_column_usage kcu
                on kcu.constraint_name = tc.constraint_name
               and kcu.table_schema = tc.table_schema
             where tc.constraint_type = 'PRIMARY KEY'
               and tc.table_schema in ({names})
            """
        )
        with self._engine.connect() as conn:
            table_rows = conn.execute(table_sql, params).fetchall()
            column_rows = conn.execute(column_sql, params).fetchall()
            pk_rows = conn.execute(pk_sql, params).fetchall()
            counts = {(_r[0], _r[1]): self._exact_count(conn, _r[0], _r[1]) for _r in table_rows}

        pks = {(r[0], r[1], r[2]) for r in pk_rows}
        columns: dict[tuple[str, str], list[RemoteColumn]] = {}
        for r in column_rows:
            key = (r[0], r[1])
            columns.setdefault(key, []).append(
                RemoteColumn(
                    name=r[2],
                    ordinal=int(r[3]),
                    data_type=str(r[4]),
                    nullable=(r[5] == "YES"),
                    default=None if r[6] is None else str(r[6]),
                    comment=None if r[7] is None else str(r[7]),
                    is_primary_key=(r[0], r[1], r[2]) in pks,
                )
            )

        result: list[RemoteTable] = []
        for r in table_rows:
            key = (r[0], r[1])
            exact = counts.get(key)
            result.append(
                RemoteTable(
                    schema=str(r[0]),
                    name=str(r[1]),
                    comment=None if r[2] is None else str(r[2]),
                    row_count=exact if exact is not None else int(r[3] or 0),
                    columns=columns.get(key, []),
                )
            )
        return result
