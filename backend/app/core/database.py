from sqlalchemy import BigInteger, Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


# 跨方言自增主键：PostgreSQL 用 BIGINT，SQLite 用 INTEGER（SQLite 只有 INTEGER 主键才自动递增）
BigIntPK = BigInteger().with_variant(Integer, "sqlite")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
