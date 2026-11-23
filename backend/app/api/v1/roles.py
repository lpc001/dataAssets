from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.services.permissions import require_any_perm, require_perm
from app.core.database import get_db
from app.crud import role as crud
from app.crud import role_data_scope as scope_crud
from app.crud import user_role as user_role_crud
from app.schemas.role import (
    RoleCreate,
    RoleRead,
    RoleUpdate,
    RoleUserIds,
    RoleUserRead,
)
from app.schemas.role_data_scope import RoleDataScopeRead, RoleDataScopeUpsert
from app.schemas.role_permission import RolePermissionRead, RolePermissionUpdate
from app.services import permissions as perm_svc

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/permissions/catalog", dependencies=[Depends(require_any_perm("system:role", "system:user"))])
def permission_catalog():
    """权限点清单，供前端渲染功能授权勾选项。"""
    from app.core.permissions import PERMISSIONS

    return [{"code": c, "name": n, "group": g} for c, n, g in PERMISSIONS]


@router.get("", response_model=list[RoleRead], dependencies=[Depends(require_any_perm("system:org", "system:user", "system:role"))])
def list_roles(db: Session = Depends(get_db)):
    return crud.list_all(db)


@router.get("/{role_id}", response_model=RoleRead, dependencies=[Depends(require_any_perm("system:org", "system:user", "system:role"))])
def get_role(role_id: int, db: Session = Depends(get_db)):
    role = crud.get(db, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    return role


@router.post("", response_model=RoleRead, status_code=201, dependencies=[Depends(require_perm("system:role"))])
def create_role(data: RoleCreate, db: Session = Depends(get_db)):
    if crud.get_by_code(db, data.code) is not None:
        raise HTTPException(status_code=400, detail="角色编码已存在")
    return crud.create(db, data)


@router.put("/{role_id}", response_model=RoleRead, dependencies=[Depends(require_perm("system:role"))])
def update_role(role_id: int, data: RoleUpdate, db: Session = Depends(get_db)):
    role = crud.get(db, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    return crud.update(db, role, data)


@router.delete("/{role_id}", status_code=204, dependencies=[Depends(require_perm("system:role"))])
def delete_role(role_id: int, db: Session = Depends(get_db)):
    role = crud.get(db, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    crud.delete(db, role)


# ---- 数据范围 ----

@router.get("/{role_id}/data-scope", response_model=RoleDataScopeRead, dependencies=[Depends(require_perm("system:role"))])
def get_data_scope(role_id: int, db: Session = Depends(get_db)):
    if crud.get(db, role_id) is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    record = scope_crud.get(db, role_id)
    if record is None:
        return RoleDataScopeRead(id=0, role_id=role_id, scope_type="ALL", custom_org_ids="")
    return record


@router.put("/{role_id}/data-scope", response_model=RoleDataScopeRead, dependencies=[Depends(require_perm("system:role"))])
def upsert_data_scope(role_id: int, data: RoleDataScopeUpsert, db: Session = Depends(get_db)):
    if crud.get(db, role_id) is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    return scope_crud.upsert(db, role_id, data)


# ---- 用户关联 ----

@router.get("/{role_id}/users", response_model=list[RoleUserRead], dependencies=[Depends(require_any_perm("system:role", "system:user"))])
def list_role_users(role_id: int, db: Session = Depends(get_db)):
    if crud.get(db, role_id) is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    return user_role_crud.list_users(db, role_id)


@router.put("/{role_id}/users", response_model=list[RoleUserRead], dependencies=[Depends(require_any_perm("system:role", "system:user"))])
def set_role_users(role_id: int, data: RoleUserIds, db: Session = Depends(get_db)):
    if crud.get(db, role_id) is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    user_role_crud.set_user_ids(db, role_id, data.user_ids)
    return user_role_crud.list_users(db, role_id)

@router.get("/{role_id}/permissions", response_model=RolePermissionRead, dependencies=[Depends(require_perm("system:role"))])
def get_role_permissions(role_id: int, db: Session = Depends(get_db)):
    role = crud.get(db, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    codes = perm_svc.role_permissions(db, role)
    return RolePermissionRead(
        role_id=role_id,
        permissions=sorted(codes),
        is_default=not bool(_raw_role_permissions(db, role_id)),
    )


@router.put("/{role_id}/permissions", response_model=RolePermissionRead, dependencies=[Depends(require_perm("system:role"))])
def update_role_permissions(role_id: int, data: RolePermissionUpdate, db: Session = Depends(get_db)):
    role = crud.get(db, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    try:
        codes = perm_svc.set_role_permissions(db, role_id, data.permissions)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RolePermissionRead(role_id=role_id, permissions=codes, is_default=not codes)


def _raw_role_permissions(db: Session, role_id: int) -> list[str]:
    from sqlalchemy import select

    from app.models.role_permission import RolePermission

    return list(
        db.scalars(select(RolePermission.perm_code).where(RolePermission.role_id == role_id)).all()
    )
