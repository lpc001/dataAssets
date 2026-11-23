from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class AssetColumn(Base):
    """资产字段：业务标注层。"""

    __tablename__ = "ast_asset_column"
    __table_args__ = (
        UniqueConstraint("asset_id", "column_name", name="uq_ast_asset_column"),
        {"comment": "数据资产字段（业务标注）"},
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    asset_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("ast_asset.id"), nullable=False, comment="所属资产ID"
    )
    resource_column_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("ast_resource_column.id"), nullable=False, comment="来源资源字段ID"
    )
    column_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="字段名")
    ordinal: Mapped[int] = mapped_column(Integer, default=0, comment="字段序号")
    business_name: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="业务中文名")
    business_meaning: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="业务含义")
    sensitive_level: Mapped[str] = mapped_column(
        String(4), nullable=False, default="L1", comment="敏感级别（L1/L2/L3）"
    )
    is_key: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否关键字段")
