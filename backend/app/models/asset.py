from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class Asset(Base):
    """登记后的数据资产：业务语义层，1 资产 = 1 张资源表。"""

    __tablename__ = "ast_asset"
    __table_args__ = {"comment": "数据资产（业务语义）"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    asset_code: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True, comment="资产编码")
    resource_table_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("ast_resource_table.id"), unique=True, nullable=False, comment="来源资源表ID"
    )
    asset_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="资产名称（业务中文名）")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="资产描述")
    domain_code: Mapped[str | None] = mapped_column(String(8), nullable=True, comment="所属数据域")
    subject_id: Mapped[int | None] = mapped_column(
        BigIntPK, ForeignKey("ast_subject.id"), nullable=True, comment="所属业务过程"
    )
    owner_domain_code: Mapped[str | None] = mapped_column(String(8), nullable=True, comment="主责域")
    trace_level: Mapped[str | None] = mapped_column(String(2), nullable=True, comment="追溯档（A/B/C/D）")
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="PUBLISHED", comment="状态（DRAFT/PUBLISHED/OFFLINE）"
    )
    owner_name: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="责任人")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="登记时间")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="最近更新时间")
