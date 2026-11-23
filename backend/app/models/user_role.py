from sqlalchemy import ForeignKey, Table, Column

from app.core.database import Base, BigIntPK

user_role = Table(
    "sys_user_role",
    Base.metadata,
    Column("user_id", BigIntPK, ForeignKey("sys_user.id"), primary_key=True, comment="用户ID"),
    Column("role_id", BigIntPK, ForeignKey("sys_role.id"), primary_key=True, comment="角色ID"),
    comment="用户角色关联表",
)
