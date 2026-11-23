"""示例数据预览：只读抽样、字段选择、可见性脱敏。"""

from sqlalchemy.orm import Session

from app.adapters.postgres import PostgresAdapter, build_url
from app.core.crypto import decrypt_text
from app.models.datasource import DataSource
from app.models.resource_table import ResourceTable

SENSITIVE_LEVELS = {"L2", "L3"}


def _url(ds: DataSource) -> str:
    return build_url(
        ds.host, ds.port, ds.database_name, ds.username, decrypt_text(ds.password_cipher)
    )


def mask_value(value, level: str):
    if value is None:
        return None
    if level == "L3":
        return "***"
    text = str(value)
    if len(text) <= 2:
        return "***"
    return f"{text[0]}***{text[-1]}"


def preview_rows(
    db: Session,
    datasource: DataSource,
    resource: ResourceTable,
    limit: int = 20,
    columns: list[str] | None = None,
    sensitive: dict[str, str] | None = None,
    mask: bool = True,
):
    """返回 (columns, rows, masked_columns)。sensitive: 列名 -> 敏感级别。"""
    adapter = PostgresAdapter(_url(datasource))
    try:
        cols, rows = adapter.fetch_sample(resource.schema_name, resource.table_name, limit, columns)
    finally:
        adapter.dispose()

    masked_columns: list[str] = []
    if mask and sensitive:
        for col in cols:
            level = sensitive.get(col)
            if level in SENSITIVE_LEVELS:
                masked_columns.append(col)
        if masked_columns:
            indexes = [i for i, c in enumerate(cols) if c in masked_columns]
            for row in rows:
                for i in indexes:
                    row[i] = mask_value(row[i], sensitive.get(cols[i], "L2"))
    return cols, rows, masked_columns
