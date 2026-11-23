from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PathOut(BaseModel):
    asset_id: int
    asset_name: str
    schema_name: str
    table_name: str
    column_name: str
    data_type: str | None = None
    domain_code: str | None = None


class ValidationSummary(BaseModel):
    block: int
    warn: int


class IndicatorCreate(BaseModel):
    indicator_code: str | None = Field(None, max_length=32)
    indicator_name: str = Field(..., max_length=128)
    domain_code: str | None = Field(None, max_length=8)
    theme: str | None = None
    indicator_level: str | None = None
    indicator_type: str | None = None
    indicator_def: str | None = None
    formula: str | None = None
    unit: str | None = None
    cycle: str | None = None
    source_asset_column_id: int
    carry_asset_column_id: int | None = None
    carry_type: str | None = None
    caliber_id: int | None = None
    owner_name: str | None = None


class IndicatorUpdate(BaseModel):
    indicator_name: str | None = Field(None, max_length=128)
    domain_code: str | None = Field(None, max_length=8)
    theme: str | None = None
    indicator_level: str | None = None
    indicator_type: str | None = None
    indicator_def: str | None = None
    formula: str | None = None
    unit: str | None = None
    cycle: str | None = None
    carry_asset_column_id: int | None = None
    carry_type: str | None = None
    caliber_id: int | None = None
    owner_name: str | None = None


class IndicatorOut(BaseModel):
    id: int
    indicator_code: str
    indicator_name: str
    domain_code: str | None
    status: str
    unit: str | None
    cycle: str | None
    owner_name: str | None
    source_path: PathOut | None = None
    carry_path: PathOut | None = None
    validation: ValidationSummary


class IndicatorDetail(IndicatorOut):
    theme: str | None
    indicator_level: str | None
    indicator_type: str | None
    indicator_def: str | None
    formula: str | None
    caliber_id: int | None
    carry_type: str | None
    source_type: str
    created_at: datetime | None
    updated_at: datetime | None
    issues: list[dict] = []
    versions: list[dict] = []


class IndicatorPage(BaseModel):
    items: list[IndicatorOut]
    total: int


class CaliberCreate(BaseModel):
    caliber_code: str = Field(..., max_length=64)
    caliber_name: str = Field(..., max_length=128)
    caliber_def: str | None = None
    formula: str | None = None
    source_fields: str | None = None
    value_type: str = "标准"
    apply_layer: str | None = None
    caliber_kind: str = "INDICATOR"


class CaliberUpdate(BaseModel):
    caliber_name: str | None = None
    caliber_def: str | None = None
    formula: str | None = None
    source_fields: str | None = None
    value_type: str | None = None
    apply_layer: str | None = None
    caliber_kind: str | None = None
    status: str | None = None


class CaliberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    caliber_code: str
    caliber_name: str
    caliber_def: str | None
    formula: str | None
    source_fields: str | None
    value_type: str
    apply_layer: str | None
    caliber_kind: str
    status: str
    owner_name: str | None


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_code: str
    rule_name: str
    target: str
    severity: str
    enabled: bool
    description: str | None
