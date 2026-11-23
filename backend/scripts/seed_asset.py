# -*- coding: utf-8 -*-
"""资产基础数据：10 个数据域 + 已打样域的业务过程。可重复执行（幂等）。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.domain import Domain  # noqa: E402
from app.models.subject import Subject  # noqa: E402

DOMAINS = [
    ("mkt", "客户与营销", True, 1, "建立/变更计费关系与计费资金流动"),
    ("prd", "生产运行", False, 2, "取水、净水工艺、药剂投加、出厂水量"),
    ("net", "管网输配", False, 3, "管网巡检、测压测流、爆管抢修、分区计量"),
    ("dsp", "供水调度", False, 4, "调度计划、水源切换、泵站启停、压力调度"),
    ("wqm", "水质监测", False, 5, "采样、实验室检测、在线监测、水质报告"),
    ("svc", "客户服务", True, 6, "服务交互，不改变计费关系、不产生资金"),
    ("ast", "资产设备", False, 7, "设备台账、维修保养、计量器具检定报废"),
    ("drn", "排水治污", False, 8, "污水收集、处理、污泥处置、再生水"),
    ("prj", "工程与项目", False, 9, "立项、招投标、合同、进度、竣工结算"),
    ("she", "安全环保", False, 10, "安全检查、隐患整改、应急管理、环保合规"),
]

SUBJECTS = [
    ("mkt", "install", "报装", 1),
    ("mkt", "reading", "抄表", 2),
    ("mkt", "billing", "计费", 3),
    ("mkt", "payment", "收费", 4),
    ("mkt", "arrears", "欠费", 5),
    ("mkt", "meter_op", "表务", 6),
    ("mkt", "biz_change", "营业变更", 7),
    ("svc", "hotline", "热线", 1),
    ("svc", "request", "服务请求", 2),
    ("svc", "work_order", "工单", 3),
    ("svc", "visit", "回访", 4),
]


def seed(db) -> None:
    for code, name, sampled, sort, desc in DOMAINS:
        row = db.query(Domain).filter(Domain.domain_code == code).first()
        if row is None:
            row = Domain(domain_code=code, domain_name=name, sampled=sampled, sort=sort, description=desc)
            db.add(row)
        else:
            row.domain_name = name
            row.sampled = sampled
            row.sort = sort
            row.description = desc
    db.commit()

    for domain_code, code, name, sort in SUBJECTS:
        row = (
            db.query(Subject)
            .filter(Subject.domain_code == domain_code, Subject.subject_code == code)
            .first()
        )
        if row is None:
            db.add(Subject(domain_code=domain_code, subject_code=code, subject_name=name, sort=sort))
    db.commit()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed(session)
        print("资产基础数据初始化完成：10 个数据域、11 个业务过程")
