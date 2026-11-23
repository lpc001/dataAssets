# -*- coding: utf-8 -*-
"""补充维度相关规则（幂等）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.governance_rule import GovernanceRule  # noqa: E402

RULES = [
    ("R12", "维度同表", "BLOCK", "维度字段必须与度量字段来自同一张资产表"),
    ("R13", "时间粒度", "BLOCK", "时间维度必须选择时间粒度"),
    ("R14", "聚合匹配", "BLOCK", "非数值字段不能求和/平均"),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        pass
    with SessionLocal() as db:
        for code, name, severity, desc in RULES:
            if db.query(GovernanceRule).filter(GovernanceRule.rule_code == code).first() is None:
                db.add(GovernanceRule(rule_code=code, rule_name=name, severity=severity, description=desc))
        db.commit()
    print("维度规则补充完成")


if __name__ == "__main__":
    main()
