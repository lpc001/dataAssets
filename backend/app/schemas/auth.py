from pydantic import BaseModel


class MeRead(BaseModel):
    id: int
    username: str
    full_name: str
    is_admin: bool
    org_id: int | None = None
    org_name: str | None = None
    roles: list[str] = []
    permissions: list[str] = []


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str
