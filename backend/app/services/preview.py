"""示例数据预览：通过数据源只读连接抽样，限行限时。"""

from sqlalchemy.orm import Session

from app.adapters.postgres import PostgresAdapter, build_url
from app.core.crypto import decrypt_text
from app.models.datasource import DataSource
from app.models.resource_table import ResourceTable


def _url(ds: DataSource) -> str:
    return build_url(
        ds.host, ds.port, ds.database_name, ds.username, decrypt_text(ds.password_cipher)
    )


def preview_rows(db: Session, datasource: DataSource, resource: ResourceTable, limit: int = 20):
    adapter = PostgresAdapter(_url(datasource))
    try:
        return adapter.fetch_sample(resource.schema_name, resource.table_name, limit)
    finally:
        adapter.dispose()
