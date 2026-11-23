from pydantic import BaseModel, ConfigDict, field_validator

VALID_SCOPE_TYPES = ("ALL", "ORG_AND_CHILD", "ORG_ONLY", "CUSTOM")


class RoleDataScopeUpsert(BaseModel):
    scope_type: str
    custom_org_ids: list[int] = []

    @field_validator("scope_type")
    @classmethod
    def check_scope_type(cls, v: str) -> str:
        if v not in VALID_SCOPE_TYPES:
            raise ValueError(f"scope_type 必须是 {VALID_SCOPE_TYPES} 之一")
        return v


class RoleDataScopeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role_id: int
    scope_type: str
    custom_org_ids: str
