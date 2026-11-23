from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


def get(db: Session, org_id: int) -> Organization | None:
    return db.get(Organization, org_id)


def list_all(db: Session) -> list[Organization]:
    return db.query(Organization).order_by(Organization.sort, Organization.id).all()


def create(db: Session, data: OrganizationCreate) -> Organization:
    org = Organization(**data.model_dump())
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def update(db: Session, org: Organization, data: OrganizationUpdate) -> Organization:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(org, key, value)
    db.commit()
    db.refresh(org)
    return org


def delete(db: Session, org: Organization) -> None:
    db.delete(org)
    db.commit()
