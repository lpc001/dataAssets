from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DomainOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain_code: str
    domain_name: str
    sort: int
    description: str | None
    asset_count: int = 0


class DomainCreate(BaseModel):
    domain_code: str = Field(..., min_length=3, max_length=8, description="域码，建议三字母小写")
    domain_name: str = Field(..., max_length=32)
    description: str | None = Field(None, max_length=500)
    sort: int = 0


class DomainPatch(BaseModel):
    domain_name: str | None = Field(None, max_length=32)
    description: str | None = Field(None, max_length=500)
    sort: int | None = None


class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain_code: str
    subject_code: str
    subject_name: str
    description: str | None
    sort: int


class ResourceTableOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    datasource_id: int
    schema_name: str
    table_name: str
    table_comment: str | None
    table_kind: str
    is_system: bool
    is_temp: bool
    row_count: int | None
    column_count: int
    suggested_layer: str | None
    suggested_domain: str | None
    suggested_trace: str | None
    remote_status: str
    registered: bool = False
    asset_id: int | None = None
    asset_status: str | None = None


class ResourceColumnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_table_id: int
    column_name: str
    ordinal: int
    data_type: str | None
    is_nullable: bool
    is_primary_key: bool
    column_comment: str | None
    is_partition_key: bool
    remote_status: str


class ResourceDetail(ResourceTableOut):
    columns: list[ResourceColumnOut] = Field(default_factory=list)


class AssetColumnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    column_name: str
    ordinal: int
    business_name: str | None
    business_meaning: str | None
    sensitive_level: str
    is_key: bool
    data_type: str | None = None
    column_comment: str | None = None


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_code: str | None
    asset_name: str
    description: str | None
    group_type: str
    domain_code: str | None
    subject_id: int | None
    owner_domain_code: str | None
    trace_level: str | None
    status: str
    owner_name: str | None
    created_at: datetime | None
    resource_table_id: int
    schema_name: str = ""
    table_name: str = ""
    data_layer: str | None = None
    row_count: int | None = None


class AssetDetail(AssetOut):
    columns: list[AssetColumnOut] = Field(default_factory=list)


class AssetPatch(BaseModel):
    asset_name: str | None = Field(None, max_length=128)
    group_type: str | None = Field(None, max_length=16)
    description: str | None = None
    domain_code: str | None = Field(None, max_length=8)
    subject_id: int | None = None
    owner_domain_code: str | None = Field(None, max_length=8)
    trace_level: str | None = Field(None, max_length=2)
    status: str | None = Field(None, max_length=16)
    owner_name: str | None = Field(None, max_length=64)


class AssetColumnPatch(BaseModel):
    business_name: str | None = Field(None, max_length=128)
    business_meaning: str | None = Field(None, max_length=500)
    sensitive_level: str | None = Field(None, max_length=4)
    is_key: bool | None = None


class RegisterItem(BaseModel):
    resource_id: int
    group_type: str | None = Field(None, max_length=16)
    asset_name: str | None = Field(None, max_length=128)
    domain_code: str | None = Field(None, max_length=8)
    trace_level: str | None = Field(None, max_length=2)
    owner_name: str | None = Field(None, max_length=64)


class RegisterRequest(BaseModel):
    datasource_id: int
    items: list[RegisterItem]


class PreviewOut(BaseModel):
    columns: list[str]
    rows: list[list]
    limit: int
    schema_name: str
    table_name: str
    masked_columns: list[str] = []
    all_columns: list[str] = []





class ResourcePatch(BaseModel):
    is_temp: bool | None = None
    is_system: bool | None = None


class ResourcePage(BaseModel):
    items: list[ResourceTableOut]
    total: int


class AssetPage(BaseModel):
    items: list[AssetOut]
    total: int


class MapDomain(BaseModel):
    domain_code: str
    domain_name: str
    asset_count: int
    column_count: int
    row_sum: int


class MapAsset(BaseModel):
    id: int
    asset_code: str | None
    asset_name: str
    table_name: str
    domain_code: str | None
    group_type: str
    layer: str | None
    rows: int | None
    columns: int
    status: str


class DataMapOut(BaseModel):
    domain_count: int
    asset_count: int
    column_count: int
    published_count: int
    domains: list[MapDomain]
    assets: list[MapAsset]


class SummaryOut(BaseModel):
    datasource_count: int
    resource_count: int
    asset_count: int
    column_count: int
    domain_count: int
    missing_count: int
