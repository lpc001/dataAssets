from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class Indicator(Base):
    __tablename__ = "ast_indicator"
    __table_args__ = {"comment": "指标主数据"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    indicator_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, comment="指标编码")
    indicator_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="指标名称")
    domain_code: Mapped[str | None] = mapped_column(String(8), nullable=True, comment="所属数据域")
    theme: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="分析主题")
    indicator_level: Mapped[str | None] = mapped_column(String(16), nullable=True, comment="分析层级")
    indicator_type: Mapped[str | None] = mapped_column(String(16), nullable=True, comment="指标类型（原子/衍生）")
    indicator_def: Mapped[str | None] = mapped_column(Text, nullable=True, comment="指标定义")
    formula: Mapped[str | None] = mapped_column(Text, nullable=True, comment="计算公式")
    unit: Mapped[str | None] = mapped_column(String(16), nullable=True, comment="单位")
    cycle: Mapped[str | None] = mapped_column(String(8), nullable=True, comment="累计周期（日/月/年）")
    source_asset_column_id: Mapped[int | None] = mapped_column(
        BigIntPK, ForeignKey("ast_asset_column.id"), nullable=True, comment="来源资产字段ID"
    )
    carry_asset_column_id: Mapped[int | None] = mapped_column(
        BigIntPK, ForeignKey("ast_asset_column.id"), nullable=True, comment="承载资产字段ID"
    )
    carry_type: Mapped[str | None] = mapped_column(String(16), nullable=True, comment="承载方式")
    caliber_id: Mapped[int | None] = mapped_column(
        BigIntPK, ForeignKey("ast_caliber.id"), nullable=True, comment="关联口径ID"
    )
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", comment="状态（DRAFT/PUBLISHED/RETIRED）")
    source_type: Mapped[str] = mapped_column(String(16), default="HUMAN", comment="来源（HUMAN/AI/IMPORT）")
    owner_name: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="责任人")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="创建时间")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="更新时间")
