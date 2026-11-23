from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class User(Base):
    __tablename__ = "sys_user"
    __table_args__ = {"comment": "系统用户"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="登录账号")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    name: Mapped[str] = mapped_column(String(64), nullable=False, default="", comment="姓名")
    org_id: Mapped[int | None] = mapped_column(
        BigIntPK, ForeignKey("sys_organization.id"), nullable=True, comment="所属组织ID"
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="ACTIVE", comment="状态（ACTIVE启用/INACTIVE停用）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, comment="创建时间"
    )
