from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class MetaChange(Base):
    """版本内的逐项变化明细（字段级）。"""

    __tablename__ = "ast_meta_change"
    __table_args__ = {"comment": "元数据变更明细"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    version_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("ast_meta_version.id"), nullable=False, comment="所属版本ID"
    )
    object_type: Mapped[str] = mapped_column(String(16), nullable=False, comment="对象类型（TABLE/COLUMN）")
    schema_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="schema 名")
    table_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="表名")
    column_name: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="字段名")
    change_type: Mapped[str] = mapped_column(String(8), nullable=False, comment="变化类型（ADD/MODIFY/DROP）")
    field_name: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="变化属性")
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True, comment="变化前")
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True, comment="变化后")
