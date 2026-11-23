from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.services.permissions import require_any_perm, require_perm
from app.core.database import get_db
from app.crud import user as crud
from app.crud import user_role as user_role_crud
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import SelfUpdate, UserCreate, UserRead, UserRoleIds, UserUpdate
from app.schemas.role import RoleRead

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_user)],
)


# ---- 个人中心（所有登录用户可用，不需要功能权限） ----


@router.get("/me", response_model=UserRead)
def get_me(current: User = Depends(get_current_user)):
    return current


@router.put("/me", response_model=UserRead)
def update_me(
    data: SelfUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.new_password:
        if not data.old_password or not verify_password(data.old_password, current.password_hash):
            raise HTTPException(status_code=400, detail="原密码不正确")
        current.password_hash = hash_password(data.new_password)
    if data.name is not None:
        current.name = data.name
    db.commit()
    db.refresh(current)
    return current


@router.get("", response_model=list[UserRead], dependencies=[Depends(require_any_perm("system:org", "system:user", "system:role"))])
def list_users(db: Session = Depends(get_db)):
    return crud.list_all(db)


@router.get("/{user_id}", response_model=UserRead, dependencies=[Depends(require_any_perm("system:org", "system:user", "system:role"))])
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("", response_model=UserRead, status_code=201, dependencies=[Depends(require_perm("system:user"))])
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    if crud.get_by_username(db, data.username) is not None:
        raise HTTPException(status_code=400, detail="用户名已存在")
    return crud.create(db, data)


@router.put("/{user_id}", response_model=UserRead, dependencies=[Depends(require_perm("system:user"))])
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    user = crud.get(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return crud.update(db, user, data)


@router.delete("/{user_id}", status_code=204, dependencies=[Depends(require_perm("system:user"))])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    crud.delete(db, user)


# ---- 用户角色关联（用户视角） ----

@router.get("/{user_id}/roles", response_model=list[RoleRead], dependencies=[Depends(require_any_perm("system:org", "system:user", "system:role"))])
def get_user_roles(user_id: int, db: Session = Depends(get_db)):
    if crud.get(db, user_id) is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user_role_crud.list_roles(db, user_id)


@router.put("/{user_id}/roles", response_model=list[RoleRead], dependencies=[Depends(require_perm("system:user"))])
def set_user_roles(user_id: int, data: UserRoleIds, db: Session = Depends(get_db)):
    if crud.get(db, user_id) is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    user_role_crud.set_role_ids(db, user_id, data.role_ids)
    return user_role_crud.list_roles(db, user_id)
