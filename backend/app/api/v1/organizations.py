from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.services.permissions import require_any_perm, require_perm
from app.core.database import get_db
from app.crud import organization as crud
from app.schemas.organization import OrganizationCreate, OrganizationRead, OrganizationUpdate

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[OrganizationRead], dependencies=[Depends(require_any_perm("system:org", "system:user", "system:role"))])
def list_organizations(db: Session = Depends(get_db)):
    return crud.list_all(db)


@router.get("/{org_id}", response_model=OrganizationRead, dependencies=[Depends(require_any_perm("system:org", "system:user", "system:role"))])
def get_organization(org_id: int, db: Session = Depends(get_db)):
    org = crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="组织不存在")
    return org


@router.post("", response_model=OrganizationRead, status_code=201, dependencies=[Depends(require_perm("system:org"))])
def create_organization(data: OrganizationCreate, db: Session = Depends(get_db)):
    return crud.create(db, data)


@router.put("/{org_id}", response_model=OrganizationRead, dependencies=[Depends(require_perm("system:org"))])
def update_organization(org_id: int, data: OrganizationUpdate, db: Session = Depends(get_db)):
    org = crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="组织不存在")
    return crud.update(db, org, data)


@router.delete("/{org_id}", status_code=204, dependencies=[Depends(require_perm("system:org"))])
def delete_organization(org_id: int, db: Session = Depends(get_db)):
    org = crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="组织不存在")
    crud.delete(db, org)
