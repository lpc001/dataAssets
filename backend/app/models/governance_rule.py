from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class GovernanceRule(Base):
    __tablename__ = "ast_governance_rule"
    __table_args__ = {"comment": "指标治理校验规则"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    rule_code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, comment="规则编码")
    rule_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="规则名称")
    target: Mapped[str] = mapped_column(String(16), default="INDICATOR", comment="适用对象")
    severity: Mapped[str] = mapped_column(String(8), default="WARN", comment="级别（BLOCK/WARN）")
    params: Mapped[str | None] = mapped_column(Text, nullable=True, comment="参数（JSON）")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="说明")
