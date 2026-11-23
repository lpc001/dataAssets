from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class RolePermission(Base):
    __tablename__ = "sys_role_permission"
    __table_args__ = (
        UniqueConstraint("role_id", "perm_code", name="uq_role_permission"),
        {"comment": "角色功能权限"},
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    role_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("sys_role.id"), nullable=False, comment="角色ID"
    )
    perm_code: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="权限编码（如 system:user、indicator:edit）"
    )
