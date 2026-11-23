from pydantic import BaseModel, ConfigDict


class OrganizationBase(BaseModel):
    code: str
    name: str
    parent_id: int | None = None
    type: str
    sort: int = 0


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None
    type: str | None = None
    sort: int | None = None


class OrganizationRead(OrganizationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
