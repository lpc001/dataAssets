from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class Caliber(Base):
    __tablename__ = "ast_caliber"
    __table_args__ = {"comment": "指标口径"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    caliber_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="口径编码")
    caliber_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="口径名称")
    caliber_def: Mapped[str | None] = mapped_column(Text, nullable=True, comment="口径说明")
    formula: Mapped[str | None] = mapped_column(Text, nullable=True, comment="计算公式")
    source_fields: Mapped[str | None] = mapped_column(Text, nullable=True, comment="依赖字段")
    value_type: Mapped[str] = mapped_column(String(16), default="标准", comment="取值类型（标准/可配置）")
    apply_layer: Mapped[str | None] = mapped_column(String(8), nullable=True, comment="适用层级（DWD/DWS）")
    caliber_kind: Mapped[str] = mapped_column(
        String(16), default="INDICATOR", comment="口径类别（INDICATOR/ENUM/SLA）"
    )
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", comment="状态（DRAFT/PUBLISHED/RETIRED）")
    source_type: Mapped[str] = mapped_column(String(16), default="HUMAN", comment="来源（HUMAN/AI/IMPORT）")
    owner_name: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="责任人")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="创建时间")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="更新时间")
