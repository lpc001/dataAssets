from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    username: str
    name: str = ""
    org_id: int | None = None
    status: str = "ACTIVE"


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    org_id: int | None = None
    status: str | None = None
    password: str | None = None


class SelfUpdate(BaseModel):
    name: str | None = None
    old_password: str | None = None
    new_password: str | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class UserRoleIds(BaseModel):
    role_ids: list[int]
