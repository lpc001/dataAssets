# -*- coding: utf-8 -*-
"""初始化指标治理规则（幂等）。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.governance_rule import GovernanceRule  # noqa: E402

RULES = [
    ("R01", "必填完整", "BLOCK", "编码/名称/定义/公式/单位/周期均必填"),
    ("R02", "编码规范", "BLOCK", "编码唯一，格式为 2 位大写字母 + 5 位数字"),
    ("R03", "来源字段有效", "BLOCK", "来源字段必须挂到已发布的资产字段"),
    ("R04", "承载字段有效", "BLOCK", "承载字段必须存在且为数值型"),
    ("R05", "公式可解析", "BLOCK", "公式不能包含中文或非法字符"),
    ("R06", "关联口径", "WARN", "指标应关联口径"),
    ("R07", "名称唯一", "WARN", "同域内指标名称不重复"),
    ("R08", "承载方式一致", "WARN", "配置项指标不挂承载字段"),
    ("R09", "单位规范", "WARN", "单位应在标准清单内"),
    ("R10", "责任人", "WARN", "已发布指标需有责任人"),
    ("R11", "域一致性", "BLOCK", "指标域与来源字段所属资产的域一致"),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for code, name, severity, desc in RULES:
            row = db.query(GovernanceRule).filter(GovernanceRule.rule_code == code).first()
            if row is None:
                db.add(GovernanceRule(rule_code=code, rule_name=name, severity=severity, description=desc))
            else:
                row.rule_name = name
                row.severity = severity
                row.description = desc
        db.commit()
    print("指标治理规则初始化完成：11 条")


if __name__ == "__main__":
    main()
