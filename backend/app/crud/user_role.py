from sqlalchemy.orm import Session

from app.models.user_role import user_role
from app.models.user import User
from app.models.role import Role


def list_user_ids(db: Session, role_id: int) -> list[int]:
    rows = db.query(user_role.c.user_id).filter(user_role.c.role_id == role_id).all()
    return [r[0] for r in rows]


def list_users(db: Session, role_id: int) -> list[User]:
    ids = list_user_ids(db, role_id)
    if not ids:
        return []
    return db.query(User).filter(User.id.in_(ids)).order_by(User.id).all()


def set_user_ids(db: Session, role_id: int, user_ids: list[int]) -> None:
    # 全量替换：先删后插
    db.execute(user_role.delete().where(user_role.c.role_id == role_id))
    for uid in user_ids:
        db.execute(user_role.insert().values(role_id=role_id, user_id=uid))
    db.commit()


# ---- 用户视角（某用户拥有哪些角色） ----

def list_role_ids(db: Session, user_id: int) -> list[int]:
    rows = db.query(user_role.c.role_id).filter(user_role.c.user_id == user_id).all()
    return [r[0] for r in rows]


def list_roles(db: Session, user_id: int) -> list[Role]:
    ids = list_role_ids(db, user_id)
    if not ids:
        return []
    return db.query(Role).filter(Role.id.in_(ids)).order_by(Role.id).all()


def set_role_ids(db: Session, user_id: int, role_ids: list[int]) -> None:
    # 全量替换：先删后插
    db.execute(user_role.delete().where(user_role.c.user_id == user_id))
    for rid in role_ids:
        db.execute(user_role.insert().values(user_id=user_id, role_id=rid))
    db.commit()
