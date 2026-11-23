from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class DataSource(Base):
    __tablename__ = "ast_datasource"
    __table_args__ = {"comment": "数据源配置"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="数据源名称")
    db_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="postgresql", comment="数据库类型（一期仅 postgresql）"
    )
    host: Mapped[str] = mapped_column(String(128), nullable=False, comment="主机地址")
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=5432, comment="端口")
    database_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="数据库名")
    schema_filter: Mapped[str] = mapped_column(
        String(255), nullable=False, default="public", comment="采集的 schema，逗号分隔"
    )
    username: Mapped[str] = mapped_column(String(64), nullable=False, comment="只读账号")
    password_cipher: Mapped[str] = mapped_column(Text, nullable=False, comment="口令密文")
    readonly_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="只读校验是否通过"
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="ACTIVE", comment="状态（ACTIVE启用/DISABLED停用）"
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="最后同步时间")
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="备注")
