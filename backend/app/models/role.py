from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class Role(Base):
    __tablename__ = "sys_role"
    __table_args__ = {"comment": "角色"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="角色名称")
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="角色编码")
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="", comment="角色描述")
