from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class ResourceTable(Base):
    """资源池中的表：技术元数据，随同步刷新，不承载业务归属。"""

    __tablename__ = "ast_resource_table"
    __table_args__ = (
        UniqueConstraint("datasource_id", "schema_name", "table_name", name="uq_ast_res_table"),
        {"comment": "资源池表（技术元数据）"},
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    datasource_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("ast_datasource.id"), nullable=False, comment="数据源ID"
    )
    schema_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="schema 名")
    table_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="表名")
    table_comment: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="远端表注释")
    table_kind: Mapped[str] = mapped_column(
        String(16), nullable=False, default="TABLE", comment="对象类型（TABLE/VIEW/MATVIEW）"
    )
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否系统表")
    is_temp: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否临时/备份表")
    row_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="最近采集行数")
    column_count: Mapped[int] = mapped_column(Integer, default=0, comment="字段数")
    suggested_layer: Mapped[str | None] = mapped_column(String(8), nullable=True, comment="建议数据类型（规则推导）")
    suggested_domain: Mapped[str | None] = mapped_column(String(8), nullable=True, comment="建议数据域（规则推导）")
    suggested_trace: Mapped[str | None] = mapped_column(String(2), nullable=True, comment="建议追溯档（规则推导）")
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="首次发现时间")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="最近发现时间")
    remote_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="ACTIVE", comment="远端状态（ACTIVE/MISSING）"
    )
