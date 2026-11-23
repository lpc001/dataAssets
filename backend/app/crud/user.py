from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def list_all(db: Session) -> list[User]:
    return db.query(User).order_by(User.id).all()


def create(db: Session, data: UserCreate) -> User:
    user = User(
        username=data.username,
        name=data.name,
        org_id=data.org_id,
        status=data.status,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update(db: Session, user: User, data: UserUpdate) -> User:
    for key, value in data.model_dump(exclude_unset=True).items():
        if key == "password" and value is not None:
            setattr(user, "password_hash", hash_password(value))
        else:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def delete(db: Session, user: User) -> None:
    from app.models.user_role import user_role

    # 先删关联，否则外键约束会挡住删除
    db.execute(user_role.delete().where(user_role.c.user_id == user.id))
    db.delete(user)
    db.commit()
