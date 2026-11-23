"""初始化脚本：创建集团组织、管理员用户与管理员角色。可重复执行（幂等）。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.role import Role
from app.models.user import User
from app.models.user_role import user_role


def seed(db: Session) -> None:
    # 组织：已有根组织（例如已用 scripts/sync_org_from_cdm.py 从 dim_org 同步过）就不再新建
    root = (
        db.query(Organization)
        .filter(Organization.parent_id.is_(None))
        .order_by(Organization.sort, Organization.id)
        .first()
    )
    if root is None:
        root = Organization(code="GROUP", name="集团", type="GROUP", sort=0)
        db.add(root)
        db.commit()
        db.refresh(root)

    # 角色
    admin_role = db.query(Role).filter(Role.code == "ADMIN").first()
    if admin_role is None:
        admin_role = Role(name="管理员", code="ADMIN", description="平台管理员")
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)

    # 管理员用户（幂等）
    admin = db.query(User).filter(User.username == "admin").first()
    if admin is None:
        admin = User(
            username="admin",
            name="系统管理员",
            password_hash=hash_password("admin123"),
            org_id=root.id,
            status="ACTIVE",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    # 绑定管理员角色（幂等）：ADMIN 角色绕过全部功能权限校验，不绑定则 admin 无任何权限
    bound = db.execute(
        select(user_role.c.user_id).where(
            user_role.c.user_id == admin.id, user_role.c.role_id == admin_role.id
        )
    ).first()
    if bound is None:
        db.execute(user_role.insert().values(user_id=admin.id, role_id=admin_role.id))
        db.commit()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
        print("种子数据初始化完成：admin / admin123")
