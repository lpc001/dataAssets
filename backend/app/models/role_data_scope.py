from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class RoleDataScope(Base):
    __tablename__ = "sys_role_data_scope"
    __table_args__ = {"comment": "角色数据权限范围"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    role_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("sys_role.id"), unique=True, nullable=False, comment="角色ID"
    )
    scope_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="ALL",
        comment="数据权限类型（ALL全部/ORG_AND_CHILD本组织及下级/ORG_ONLY本级/CUSTOM自定义）",
    )
    custom_org_ids: Mapped[str] = mapped_column(
        Text, nullable=False, default="", comment="自定义组织ID列表（scope_type=CUSTOM时有效，逗号分隔，如 1,3,5）"
    )
