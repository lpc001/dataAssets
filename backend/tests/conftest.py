import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.role import Role
from app.models.user import User
from app.models.user_role import user_role


def _ensure_test_admin(db) -> None:
    """测试管理员：拥有 ADMIN 角色，绕过功能权限校验。"""
    user = db.query(User).filter(User.username == "test_admin").first()
    if user is None:
        user = User(
            username="test_admin",
            name="测试管理员",
            password_hash=hash_password("secret123"),
            status="ACTIVE",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    role = db.query(Role).filter(Role.code == "ADMIN").first()
    if role is None:
        role = Role(name="系统管理员", code="ADMIN", description="")
        db.add(role)
        db.commit()
        db.refresh(role)
    exists = db.execute(
        user_role.select().where(
            (user_role.c.user_id == user.id) & (user_role.c.role_id == role.id)
        )
    ).first()
    if not exists:
        db.execute(user_role.insert().values(user_id=user.id, role_id=role.id))
        db.commit()


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def anon_client(db_session):
    """未登录的测试客户端，供认证相关测试使用。"""
    _ensure_test_admin(db_session)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client(db_session):
    """已登录（携带 Bearer token）的测试客户端，供受保护的管理接口测试使用。"""
    _ensure_test_admin(db_session)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        resp = c.post(
            "/api/v1/auth/login",
            data={"username": "test_admin", "password": "secret123"},
        )
        assert resp.status_code == 200
        c.headers["Authorization"] = f"Bearer {resp.json()['access_token']}"
        yield c
    app.dependency_overrides.clear()
