from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class IndicatorDimension(Base):
    __tablename__ = "ast_indicator_dimension"
    __table_args__ = (
        UniqueConstraint("indicator_id", "asset_column_id", name="uq_ast_ind_dim"),
        {"comment": "指标维度字段"},
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    indicator_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("ast_indicator.id"), nullable=False, comment="指标ID"
    )
    asset_column_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("ast_asset_column.id"), nullable=False, comment="维度资产字段ID"
    )
    dimension_type: Mapped[str] = mapped_column(
        String(16), default="CATEGORY", comment="维度类型（TIME/CATEGORY）"
    )
    time_grain: Mapped[str | None] = mapped_column(
        String(8), nullable=True, comment="时间粒度（YEAR/QUARTER/MONTH/DAY）"
    )
    alias: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="显示名")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
