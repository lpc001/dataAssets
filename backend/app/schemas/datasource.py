from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DataSourceBase(BaseModel):
    name: str = Field(..., max_length=64, description="数据源名称")
    host: str = Field(..., max_length=128, description="主机地址")
    port: int = Field(5432, description="端口")
    database_name: str = Field(..., max_length=64, description="数据库名")
    schema_filter: str = Field("public", max_length=255, description="采集的 schema，逗号分隔")
    username: str = Field(..., max_length=64, description="只读账号")
    remark: str | None = Field(None, max_length=255, description="备注")


class DataSourceCreate(DataSourceBase):
    password: str = Field(..., min_length=1, description="口令（仅写入，不回显）")


class DataSourceUpdate(BaseModel):
    name: str | None = Field(None, max_length=64)
    host: str | None = Field(None, max_length=128)
    port: int | None = None
    database_name: str | None = Field(None, max_length=64)
    schema_filter: str | None = Field(None, max_length=255)
    username: str | None = Field(None, max_length=64)
    password: str | None = Field(None, description="不传则保持原口令")
    status: str | None = Field(None, description="ACTIVE/DISABLED")
    remark: str | None = Field(None, max_length=255)


class DataSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    db_type: str
    host: str
    port: int
    database_name: str
    schema_filter: str
    username: str
    readonly_verified: bool
    status: str
    last_sync_at: datetime | None
    remark: str | None


class SchemaQueryIn(BaseModel):
    host: str
    port: int = 5432
    database_name: str
    username: str
    password: str | None = None
    datasource_id: int | None = None


class SchemaListOut(BaseModel):
    schemas: list[str]


class ConnectionTestResult(BaseModel):
    ok: bool
    readonly: bool
    message: str


class MetaVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    datasource_id: int
    version_no: int
    started_at: datetime
    finished_at: datetime | None
    status: str
    table_added: int
    table_changed: int
    table_dropped: int
    column_added: int
    column_changed: int
    column_dropped: int
    operator: str | None
    message: str | None


class MetaChangeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_id: int
    object_type: str
    schema_name: str
    table_name: str
    column_name: str | None
    change_type: str
    field_name: str | None
    old_value: str | None
    new_value: str | None
