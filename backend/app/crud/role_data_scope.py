from sqlalchemy.orm import Session

from app.models.role_data_scope import RoleDataScope
from app.schemas.role_data_scope import RoleDataScopeUpsert


def get(db: Session, role_id: int) -> RoleDataScope | None:
    return db.query(RoleDataScope).filter(RoleDataScope.role_id == role_id).first()


def upsert(db: Session, role_id: int, data: RoleDataScopeUpsert) -> RoleDataScope:
    custom = ",".join(str(i) for i in data.custom_org_ids)
    record = get(db, role_id)
    if record is None:
        record = RoleDataScope(role_id=role_id, scope_type=data.scope_type, custom_org_ids=custom)
        db.add(record)
    else:
        record.scope_type = data.scope_type
        record.custom_org_ids = custom
    db.commit()
    db.refresh(record)
    return record
