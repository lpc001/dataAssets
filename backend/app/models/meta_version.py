from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class MetaVersion(Base):
    """一次元数据采集的版本记录。"""

    __tablename__ = "ast_meta_version"
    __table_args__ = (
        UniqueConstraint("datasource_id", "version_no", name="uq_ast_meta_version"),
        {"comment": "元数据采集版本"},
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    datasource_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("ast_datasource.id"), nullable=False, comment="数据源ID"
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, comment="版本号（按数据源自增）")
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="开始时间")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="结束时间")
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="RUNNING", comment="状态（RUNNING/SUCCESS/FAILED）"
    )
    table_added: Mapped[int] = mapped_column(Integer, default=0, comment="新增表数")
    table_changed: Mapped[int] = mapped_column(Integer, default=0, comment="变更表数")
    table_dropped: Mapped[int] = mapped_column(Integer, default=0, comment="消失表数")
    column_added: Mapped[int] = mapped_column(Integer, default=0, comment="新增字段数")
    column_changed: Mapped[int] = mapped_column(Integer, default=0, comment="变更字段数")
    column_dropped: Mapped[int] = mapped_column(Integer, default=0, comment="消失字段数")
    operator: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="操作人")
    message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="摘要或错误信息")
