from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class IndicatorVersion(Base):
    __tablename__ = "ast_indicator_version"
    __table_args__ = {"comment": "指标/口径变更历史"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    object_type: Mapped[str] = mapped_column(String(16), nullable=False, comment="对象类型（INDICATOR/CALIBER）")
    object_id: Mapped[int] = mapped_column(BigIntPK, nullable=False, comment="对象ID")
    version_no: Mapped[int] = mapped_column(Integer, default=1, comment="版本号")
    changed_by: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="修改人")
    changed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="修改时间")
    changes: Mapped[str | None] = mapped_column(Text, nullable=True, comment="变更内容JSON")
    comment: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="备注")
