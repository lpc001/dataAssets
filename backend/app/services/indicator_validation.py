"""指标校验：规则驱动，返回阻断/警告问题清单。"""

import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.asset_column import AssetColumn
from app.models.governance_rule import GovernanceRule
from app.models.indicator import Indicator
from app.models.indicator_dimension import IndicatorDimension
from app.models.resource_column import ResourceColumn

CODE_RE = re.compile(r"^[A-Z]{2}\d{5}$")
FORMULA_RE = re.compile(r"^[A-Za-z0-9_.+\-*/()%<>= ,]+$")
NUMERIC_HINTS = ("int", "numeric", "decimal", "float", "double", "real", "money", "number")
ALLOWED_UNITS = {"%", "元", "m³", "户", "个", "次", "小时", "分钟", "秒", "户/月", "元/m³"}

REQUIRED_FIELDS = [
    ("indicator_code", "指标编码"),
    ("indicator_name", "指标名称"),
    ("indicator_def", "指标定义"),
    ("formula", "计算公式"),
    ("unit", "单位"),
    ("cycle", "累计周期"),
]


def _issue(code: str, name: str, severity: str, message: str) -> dict:
    return {"rule_code": code, "rule_name": name, "severity": severity, "message": message}


def _source_asset(db: Session, indicator: Indicator):
    if not indicator.source_asset_column_id:
        return None, None
    column = db.get(AssetColumn, indicator.source_asset_column_id)
    if column is None:
        return None, None
    asset = db.get(Asset, column.asset_id)
    return column, asset


def validate_indicator(db: Session, indicator: Indicator, enabled: set[str] | None = None) -> list[dict]:
    issues: list[dict] = []
    source_col, source_asset = _source_asset(db, indicator)

    def on(code: str) -> bool:
        return enabled is None or code in enabled

    if on("R01"):
        missing = [label for attr, label in REQUIRED_FIELDS if not str(getattr(indicator, attr) or "").strip()]
        if missing:
            issues.append(_issue("R01", "必填完整", "BLOCK", "缺少：" + "、".join(missing)))

    if on("R02") and indicator.indicator_code:
        if not CODE_RE.match(indicator.indicator_code):
            issues.append(_issue("R02", "编码规范", "BLOCK", "编码应为 2 位大写字母 + 5 位数字，如 BM03008"))
        duplicate = db.scalars(
            select(Indicator).where(
                Indicator.indicator_code == indicator.indicator_code,
                Indicator.id != (indicator.id or 0),
            )
        ).first()
        if duplicate:
            issues.append(_issue("R02", "编码规范", "BLOCK", "编码已被其他指标使用"))

    if on("R03"):
        if source_col is None or source_asset is None:
            issues.append(_issue("R03", "来源字段有效", "BLOCK", "未挂载来源资产字段"))
        elif source_asset.status != "PUBLISHED":
            issues.append(
                _issue("R03", "来源字段有效", "BLOCK", f"来源资产当前状态为 {source_asset.status}，需已发布")
            )

    if on("R04") and indicator.carry_asset_column_id:
        carry = db.get(AssetColumn, indicator.carry_asset_column_id)
        if carry is None:
            issues.append(_issue("R04", "承载字段有效", "BLOCK", "承载字段不存在"))
        else:
            rc = db.get(ResourceColumn, carry.resource_column_id)
            dtype = (rc.data_type or "").lower() if rc else ""
            if dtype and not any(h in dtype for h in NUMERIC_HINTS):
                issues.append(_issue("R04", "承载字段有效", "BLOCK", f"承载字段类型为 {dtype}，非数值型"))

    if on("R05") and indicator.formula:
        if not FORMULA_RE.match(indicator.formula.strip()):
            issues.append(
                _issue("R05", "公式可解析", "BLOCK", "公式含中文或非法字符，需用字段名与运算符表达")
            )

    if on("R06") and not indicator.caliber_id:
        issues.append(_issue("R06", "关联口径", "WARN", "未关联口径"))

    if on("R07") and indicator.indicator_name:
        dup = db.scalars(
            select(Indicator).where(
                Indicator.indicator_name == indicator.indicator_name,
                Indicator.domain_code == indicator.domain_code,
                Indicator.id != (indicator.id or 0),
            )
        ).first()
        if dup:
            issues.append(_issue("R07", "名称唯一", "WARN", "同域内已存在同名指标"))

    if on("R08") and indicator.carry_type == "配置项" and indicator.carry_asset_column_id:
        issues.append(_issue("R08", "承载方式一致", "WARN", "配置项指标不应挂承载字段"))

    if on("R09") and indicator.unit and indicator.unit not in ALLOWED_UNITS:
        issues.append(_issue("R09", "单位规范", "WARN", f"单位「{indicator.unit}」不在标准清单内"))

    if on("R10") and indicator.status == "PUBLISHED" and not indicator.owner_name:
        issues.append(_issue("R10", "责任人", "WARN", "已发布指标应填写责任人"))

    if on("R11"):
        if source_asset is not None and indicator.domain_code and source_asset.domain_code != indicator.domain_code:
            issues.append(
                _issue(
                    "R11",
                    "域一致性",
                    "BLOCK",
                    f"来源字段属于 {source_asset.domain_code or '公共'}，与指标域 {indicator.domain_code} 不一致",
                )
            )

    dimensions = []
    if indicator.id:
        dimensions = db.scalars(
            select(IndicatorDimension).where(IndicatorDimension.indicator_id == indicator.id)
        ).all()

    if on("R12"):
        for dim in dimensions:
            column = db.get(AssetColumn, dim.asset_column_id)
            if column is None or source_col is None or column.asset_id != source_col.asset_id:
                issues.append(_issue("R12", "维度同表", "BLOCK", "维度字段必须与度量字段来自同一张资产表"))

    if on("R13"):
        for dim in dimensions:
            if dim.dimension_type == "TIME" and not dim.time_grain:
                issues.append(_issue("R13", "时间粒度", "BLOCK", "时间维度必须选择时间粒度（年/季/月/日）"))

    if on("R14") and source_col is not None and indicator.aggregation in {"SUM", "AVG"}:
        rc = db.get(ResourceColumn, source_col.resource_column_id)
        dtype = (rc.data_type or "").lower() if rc else ""
        if dtype and not any(h in dtype for h in NUMERIC_HINTS):
            issues.append(
                _issue("R14", "聚合匹配", "BLOCK", f"度量字段类型为 {dtype}，不能使用求和/平均")
            )

    return issues


def enabled_rules(db: Session) -> set[str] | None:
    """规则表为空时视为全部启用（便于新环境与测试）。"""
    rows = db.scalars(select(GovernanceRule).where(GovernanceRule.enabled.is_(True))).all()
    return {r.rule_code for r in rows} if rows else None


def summarize(issues: list[dict]) -> dict:
    return {
        "block": sum(1 for i in issues if i["severity"] == "BLOCK"),
        "warn": sum(1 for i in issues if i["severity"] == "WARN"),
        "issues": issues,
    }
