"""目标库元数据适配器的公共契约。"""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class RemoteColumn:
    name: str
    ordinal: int
    data_type: str
    nullable: bool
    default: str | None
    comment: str | None
    is_primary_key: bool = False


@dataclass
class RemoteTable:
    schema: str
    name: str
    comment: str | None
    row_count: int | None
    columns: list[RemoteColumn] = field(default_factory=list)


class MetadataAdapter(Protocol):
    """数据源适配器：一期仅 PostgreSQL 实现，接口为后续 MySQL/Hive 预留。"""

    def test_connection(self) -> tuple[bool, str]: ...

    def is_readonly(self) -> bool: ...

    def fetch_tables(self, schemas: list[str]) -> list[RemoteTable]: ...
