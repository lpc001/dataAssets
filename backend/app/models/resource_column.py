from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class ResourceColumn(Base):
    """资源池字段：技术元数据。"""

    __tablename__ = "ast_resource_column"
    __table_args__ = (
        UniqueConstraint("resource_table_id", "column_name", name="uq_ast_res_column"),
        {"comment": "资源池字段（技术元数据）"},
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    resource_table_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("ast_resource_table.id"), nullable=False, comment="所属资源表ID"
    )
    column_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="字段名")
    ordinal: Mapped[int] = mapped_column(Integer, default=0, comment="字段序号")
    data_type: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="数据类型")
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否可空")
    column_default: Mapped[str | None] = mapped_column(Text, nullable=True, comment="默认值")
    is_primary_key: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否主键")
    column_comment: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="远端字段注释")
    is_partition_key: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否分区键")
    remote_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="ACTIVE", comment="远端状态（ACTIVE/MISSING）"
    )
