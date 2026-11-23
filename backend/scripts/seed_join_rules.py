# -*- coding: utf-8 -*-
"""补充关联资产规则。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.governance_rule import GovernanceRule  # noqa: E402

RULES = [
    ("R15", "关联资产有效", "BLOCK", "关联资产必须存在且已发布"),
    ("R16", "关联同源", "BLOCK", "关联资产需同一数据源，关联字段需属于对应资产"),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for code, name, severity, desc in RULES:
            if db.query(GovernanceRule).filter(GovernanceRule.rule_code == code).first() is None:
                db.add(GovernanceRule(rule_code=code, rule_name=name, severity=severity, description=desc))
        db.commit()
    print("关联规则补充完成")


if __name__ == "__main__":
    main()
