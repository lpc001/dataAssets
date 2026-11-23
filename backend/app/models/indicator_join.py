from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class IndicatorJoin(Base):
    __tablename__ = "ast_indicator_join"
    __table_args__ = (
        UniqueConstraint("indicator_id", "asset_id", name="uq_ast_ind_join"),
        {"comment": "指标关联资产"},
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    indicator_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("ast_indicator.id"), nullable=False, comment="指标ID"
    )
    asset_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("ast_asset.id"), nullable=False, comment="关联资产ID"
    )
    left_asset_column_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("ast_asset_column.id"), nullable=False, comment="主表关联字段ID"
    )
    right_asset_column_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("ast_asset_column.id"), nullable=False, comment="关联表关联字段ID"
    )
    join_type: Mapped[str] = mapped_column(String(8), default="LEFT", comment="关联方式（LEFT/INNER）")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
