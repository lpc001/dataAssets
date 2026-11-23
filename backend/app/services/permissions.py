"""功能权限的读取与校验。"""

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.permissions import (
    ADMIN_ROLE_CODE,
    DEFAULT_ROLE_PERMISSIONS,
    perm_name,
)
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import user_role


def user_roles(db: Session, user: User) -> list[Role]:
    return list(
        db.scalars(
            select(Role).join(user_role, user_role.c.role_id == Role.id).where(user_role.c.user_id == user.id)
        ).all()
    )


def is_admin(db: Session, user: User) -> bool:
    return any(role.code == ADMIN_ROLE_CODE for role in user_roles(db, user))


def role_permissions(db: Session, role: Role) -> set[str]:
    """角色权限：没有任何记录时按默认权限（只看指标）处理。"""
    codes = set(
        db.scalars(select(RolePermission.perm_code).where(RolePermission.role_id == role.id)).all()
    )
    return codes if codes else set(DEFAULT_ROLE_PERMISSIONS)


def permissions_for_user(db: Session, user: User) -> set[str]:
    roles = user_roles(db, user)
    if any(role.code == ADMIN_ROLE_CODE for role in roles):
        from app.core.permissions import all_codes

        return set(all_codes())
    codes: set[str] = set()
    for role in roles:
        codes |= role_permissions(db, role)
    return codes


def has_perm(db: Session, user: User, code: str) -> bool:
    return code in permissions_for_user(db, user)


def require_perm(code: str):
    """FastAPI 依赖：校验当前用户拥有指定功能权限。"""

    def _dep(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if not has_perm(db, user, code):
            raise HTTPException(status_code=403, detail=f"没有该操作权限：{perm_name(code)}")
        return user

    return _dep


def require_any_perm(*codes: str):
    """FastAPI 依赖：拥有其中任意一个功能权限即可。"""

    def _dep(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        granted = permissions_for_user(db, user)
        if not granted.intersection(codes):
            names = "、".join(perm_name(c) for c in codes)
            raise HTTPException(status_code=403, detail=f"没有该操作权限：{names}")
        return user

    return _dep


def set_role_permissions(db: Session, role_id: int, codes: list[str]) -> list[str]:
    from app.core.permissions import all_codes

    valid = set(all_codes())
    unknown = [c for c in codes if c not in valid]
    if unknown:
        raise ValueError(f"未知的权限编码：{', '.join(unknown)}")
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    seen: set[str] = set()
    for code in codes:
        if code in seen:
            continue
        seen.add(code)
        db.add(RolePermission(role_id=role_id, perm_code=code))
    db.commit()
    return sorted(seen)
