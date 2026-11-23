from sqlalchemy.orm import Session

from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate


def get(db: Session, role_id: int) -> Role | None:
    return db.get(Role, role_id)


def get_by_code(db: Session, code: str) -> Role | None:
    return db.query(Role).filter(Role.code == code).first()


def list_all(db: Session) -> list[Role]:
    return db.query(Role).order_by(Role.id).all()


def create(db: Session, data: RoleCreate) -> Role:
    role = Role(**data.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update(db: Session, role: Role, data: RoleUpdate) -> Role:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(role, key, value)
    db.commit()
    db.refresh(role)
    return role


def delete(db: Session, role: Role) -> None:
    from app.models.role_data_scope import RoleDataScope
    from app.models.role_permission import RolePermission
    from app.models.user_role import user_role

    # 先清掉三张关联表，否则外键约束会挡住删除
    db.execute(user_role.delete().where(user_role.c.role_id == role.id))
    db.query(RoleDataScope).filter(RoleDataScope.role_id == role.id).delete()
    db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
    db.delete(role)
    db.commit()
