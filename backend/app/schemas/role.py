from pydantic import BaseModel, ConfigDict


class RoleBase(BaseModel):
    name: str
    code: str
    description: str = ""


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class RoleRead(RoleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class RoleUserIds(BaseModel):
    user_ids: list[int]


class RoleUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    name: str
    org_id: int | None
    status: str
