# -*- coding: utf-8 -*-
"""数据权限范围解析：把角色配置的数据范围换算成可访问的组织集合。

语义与前端「数据权限」一致：
- ALL             全部组织；
- ORG_AND_CHILD   本组织及下级；
- ORG_ONLY        仅本组织；
- CUSTOM          自选组织。
角色没有任何数据范围记录时按 ALL 处理（与角色管理页的默认值一致）。
ADMIN 角色直接视为全部。
"""
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.role_data_scope import RoleDataScope
from app.models.user import User
from app.services.permissions import is_admin, user_roles


def _children_ids(db: Session, org_id: int) -> list[int]:
    """本组织及全部下级的组织 ID（广度遍历，防御环）。"""
    pairs = db.query(Organization.id, Organization.parent_id).all()
    children: dict[int | None, list[int]] = {}
    for oid, pid in pairs:
        children.setdefault(pid, []).append(oid)

    out: list[int] = []
    seen: set[int] = set()
    stack = [org_id]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        out.append(current)
        stack.extend(children.get(current, []))
    return out


def allowed_org_ids(db: Session, user: User) -> list[int] | None:
    """None 表示不限制（全部组织）；列表表示仅限这些组织，空列表表示无任何数据权限。"""
    if is_admin(db, user):
        return None

    ids: set[int] = set()
    for role in user_roles(db, user):
        record = (
            db.query(RoleDataScope).filter(RoleDataScope.role_id == role.id).first()
        )
        scope_type = ((record.scope_type if record else "ALL") or "ALL").strip().upper()

        if scope_type == "ALL":
            return None
        if scope_type == "ORG_AND_CHILD":
            if user.org_id:
                ids.update(_children_ids(db, user.org_id))
        elif scope_type == "ORG_ONLY":
            if user.org_id:
                ids.add(user.org_id)
        elif scope_type == "CUSTOM":
            for part in ((record.custom_org_ids if record else "") or "").split(","):
                part = part.strip()
                if part.isdigit():
                    ids.add(int(part))
    return sorted(ids)


def allowed_org_codes(db: Session, user: User) -> list[str] | None:
    """组织 ID 换成组织编码（取数配置里存的是 org_code）。"""
    ids = allowed_org_ids(db, user)
    if ids is None:
        return None
    if not ids:
        return []
    rows = db.query(Organization.code).filter(Organization.id.in_(ids)).all()
    return sorted({code for (code,) in rows})
