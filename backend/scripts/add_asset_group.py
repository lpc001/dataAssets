# -*- coding: utf-8 -*-
"""为资产补充归类字段（业务域/公共维度/跨域专题/未归类）并回填存量数据。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text  # noqa: E402

import app.models  # noqa: F401,E402
from app.core.database import Base, engine  # noqa: E402

STEPS = [
    "alter table ast_asset add column if not exists group_type varchar(16)",
    "update ast_asset set group_type = 'DOMAIN' where group_type is null",
    "alter table ast_asset alter column group_type set default 'DOMAIN'",
    "alter table ast_asset alter column group_type set not null",
    """
    update ast_asset a
       set group_type = case
             when rt.suggested_layer = 'DIM' then 'PUBLIC'
             when rt.suggested_layer = 'DWS' and a.domain_code is null then 'TOPIC'
             when a.domain_code is null then 'OTHER'
             else 'DOMAIN'
           end
      from ast_resource_table rt
     where rt.id = a.resource_table_id
       and a.group_type = 'DOMAIN'
    """,
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        for sql in STEPS:
            conn.execute(text(sql))
        rows = conn.execute(
            text("select group_type, count(*) from ast_asset group by 1 order by 1")
        ).all()
    print("资产归类回填完成：", [(r[0], r[1]) for r in rows])


if __name__ == "__main__":
    main()
