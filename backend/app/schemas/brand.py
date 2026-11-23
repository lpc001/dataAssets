from pydantic import BaseModel, ConfigDict


class BrandBase(BaseModel):
    name: str = ""
    subtitle: str = ""
    logo: str = ""


class BrandUpdate(BaseModel):
    name: str | None = None
    subtitle: str | None = None
    logo: str | None = None


class BrandRead(BrandBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
