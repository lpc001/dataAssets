from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.crud import user as user_crud
from app.models.organization import Organization
from app.schemas.auth import MeRead, Token
from app.services import permissions as perm_svc

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = user_crud.get_by_username(db, form.username)
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="用户已停用")
    return Token(access_token=create_access_token(user.username))


@router.get("/me", response_model=MeRead)
def me(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    roles = perm_svc.user_roles(db, user)
    org = db.get(Organization, user.org_id) if user.org_id else None
    return MeRead(
        id=user.id,
        username=user.username,
        full_name=user.name,
        is_admin=perm_svc.is_admin(db, user),
        org_id=user.org_id,
        org_name=org.name if org else None,
        roles=[role.name for role in roles],
        permissions=sorted(perm_svc.permissions_for_user(db, user)),
    )
