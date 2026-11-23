"""按表命名规则自动归类：分层、数据域、追溯档，以及系统表/临时表识别。

规则来源：《客户与营销域数据模型打样_V2.md》3.1 命名规范、《规范_数据域切分判断标准.md》。
注意：这些只是「建议」，登记资产时由人确认，规则不再直接决定业务归属。
"""

import re

DOMAIN_CODES: dict[str, str] = {
    "mkt": "客户与营销",
    "prd": "生产运行",
    "net": "管网输配",
    "dsp": "供水调度",
    "wqm": "水质监测",
    "svc": "客户服务",
    "ast": "资产设备",
    "drn": "排水治污",
    "prj": "工程与项目",
    "she": "安全环保",
}

_DIM_RE = re.compile(r"^dim_", re.IGNORECASE)
_FACT_RE = re.compile(r"^(dwd|dws)_([a-z]{3})_", re.IGNORECASE)
_NRW_RE = re.compile(r"^dws_nrw_", re.IGNORECASE)
_TEMP_RE = re.compile(r"(^|_)(tmp|temp|bak|backup|old|copy|test)(_|$)", re.IGNORECASE)
_SYSTEM_SCHEMAS = {"pg_catalog", "information_schema"}


def classify_table(table_name: str) -> tuple[str, str | None, str | None]:
    """返回 (建议数据类型, 建议数据域, 建议追溯档)。

    - dim_*       → DIM / 公共（无域）/ C 主数据
    - dwd_{域}_*  → DWD / 该域 / A 逐条对账
    - dws_{域}_*  → DWS / 该域 / D 汇总
    - dws_nrw_*   → DWS / 跨域专题（无域）/ D
    """
    name = (table_name or "").strip().lower()
    if _DIM_RE.match(name):
        return "DIM", None, "C"
    if _NRW_RE.match(name):
        return "DWS", None, "D"
    match = _FACT_RE.match(name)
    if match:
        layer, code = match.group(1), match.group(2)
        domain = code if code in DOMAIN_CODES else None
        return layer.upper(), domain, ("A" if layer.lower() == "dwd" else "D")
    return "OTHER", None, None


def owner_domain(table_name: str, domain_code: str | None) -> str | None:
    """公共维度的主责域：dim_cust / dim_meter 主责客户与营销域。"""
    name = (table_name or "").lower()
    if name in {"dim_cust", "dim_meter"}:
        return "mkt"
    return domain_code


def table_kind(relkind: str | None) -> str:
    return {"r": "TABLE", "p": "TABLE", "v": "VIEW", "m": "MATVIEW", "f": "FOREIGN"}.get(
        (relkind or "r").lower(), "TABLE"
    )


def detect_system(schema_name: str, table_name: str) -> bool:
    return schema_name.lower() in _SYSTEM_SCHEMAS or table_name.lower().startswith("pg_")


def detect_temp(table_name: str) -> bool:
    return bool(_TEMP_RE.search(table_name or ""))
