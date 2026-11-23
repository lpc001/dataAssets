from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crypto import encrypt_text
from app.models.datasource import DataSource
from app.models.meta_change import MetaChange
from app.models.meta_version import MetaVersion
from app.schemas.datasource import DataSourceCreate, DataSourceUpdate


def list_all(db: Session) -> list[DataSource]:
    return list(db.scalars(select(DataSource).order_by(DataSource.id)).all())


def get(db: Session, datasource_id: int) -> DataSource | None:
    return db.get(DataSource, datasource_id)


def get_by_name(db: Session, name: str) -> DataSource | None:
    return db.scalars(select(DataSource).where(DataSource.name == name)).first()


def create(db: Session, payload: DataSourceCreate) -> DataSource:
    row = DataSource(
        name=payload.name,
        db_type="postgresql",
        host=payload.host,
        port=payload.port,
        database_name=payload.database_name,
        schema_filter=payload.schema_filter,
        username=payload.username,
        password_cipher=encrypt_text(payload.password),
        remark=payload.remark,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update(db: Session, row: DataSource, payload: DataSourceUpdate) -> DataSource:
    data = payload.model_dump(exclude_unset=True)
    password = data.pop("password", None)
    for key, value in data.items():
        setattr(row, key, value)
    if password:
        row.password_cipher = encrypt_text(password)
    db.commit()
    db.refresh(row)
    return row


def remove(db: Session, row: DataSource) -> None:
    db.delete(row)
    db.commit()


def list_versions(db: Session, datasource_id: int, limit: int = 30) -> list[MetaVersion]:
    return list(
        db.scalars(
            select(MetaVersion)
            .where(MetaVersion.datasource_id == datasource_id)
            .order_by(MetaVersion.version_no.desc())
            .limit(limit)
        ).all()
    )


def list_changes(db: Session, version_id: int) -> list[MetaChange]:
    return list(
        db.scalars(
            select(MetaChange).where(MetaChange.version_id == version_id).order_by(MetaChange.id)
        ).all()
    )
