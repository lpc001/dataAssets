# -*- coding: utf-8 -*-
"""设置系统品牌（名称 + Logo）。

用法（在 backend 目录下）：
    python -X utf8 scripts/seed_brand.py --name "某某平台" --subtitle "副标题"
    python -X utf8 scripts/seed_brand.py --reset

Logo 也可以在「系统管理 → 品牌设置」页面上传，这里只负责名称。
"""
import argparse
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import Settings  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.models.brand import Brand  # noqa: E402

from app.services.brand import DEFAULT_NAME, DEFAULT_SUBTITLE  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default=DEFAULT_NAME, help="系统名称")
    parser.add_argument("--subtitle", default=DEFAULT_SUBTITLE, help="副标题")
    parser.add_argument("--reset", action="store_true", help="恢复默认品牌")
    args = parser.parse_args()

    settings = Settings()
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    with Session() as db:
        row = db.query(Brand).order_by(Brand.id).first()
        if row is None:
            row = Brand(name=DEFAULT_NAME, subtitle=DEFAULT_SUBTITLE)
            db.add(row)
        if args.reset:
            row.name = DEFAULT_NAME
            row.subtitle = DEFAULT_SUBTITLE
            row.logo = ""
            print("[RESET] 已恢复默认品牌：" + DEFAULT_NAME)
        else:
            row.name = args.name
            row.subtitle = args.subtitle
            print("[DONE] 品牌已设为：" + args.name)
        db.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
