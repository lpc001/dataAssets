# -*- coding: utf-8 -*-
"""品牌配置读取与更新。

单行配置：库里没有记录时返回内置默认（水投·指标平台），不清库也能用。
Logo 存 base64 data URL，避免额外的静态文件目录与部署依赖。
"""
from sqlalchemy.orm import Session

from app.models.brand import Brand

DEFAULT_LOGO = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2NCA2NCI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImciIHgxPSIwIiB5MT0iMCIgeDI9IjEiIHkyPSIxIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwIiBzdG9wLWNvbG9yPSIjNEZDM0Y3Ii8+CiAgICAgIDxzdG9wIG9mZnNldD0iMSIgc3RvcC1jb2xvcj0iIzBENDdBMSIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KICA8L2RlZnM+CiAgPGNpcmNsZSBjeD0iMzIiIGN5PSIzMiIgcj0iMzAiIGZpbGw9InVybCgjZykiLz4KICA8ZWxsaXBzZSBjeD0iMzIiIGN5PSIzMyIgcng9IjIzIiByeT0iOCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmZmZmIiBzdHJva2Utb3BhY2l0eT0iMC40NSIgc3Ryb2tlLXdpZHRoPSIyIiB0cmFuc2Zvcm09InJvdGF0ZSgtMjQgMzIgMzMpIi8+CiAgPHBhdGggZD0iTTMyIDEzYzYuMiA4LjQgMTIuNSAxNC42IDEyLjUgMjEuNmExMi41IDEyLjUgMCAwIDEtMjUgMEMxOS41IDI3LjYgMjUuOCAyMS40IDMyIDEzeiIgZmlsbD0iI2ZmZmZmZiIgb3BhY2l0eT0iMC45NiIvPgogIDxjaXJjbGUgY3g9IjI2IiBjeT0iMzMiIHI9IjIuNiIgZmlsbD0iIzE1NjVDMCIgb3BhY2l0eT0iMC4yNSIvPgo8L3N2Zz4="

DEFAULT_NAME = "水投·指标平台"
DEFAULT_SUBTITLE = "登录后进入指标管理"

MAX_LOGO_BYTES = 512 * 1024


class BrandError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _default_payload() -> dict:
    return {"id": 0, "name": DEFAULT_NAME, "subtitle": DEFAULT_SUBTITLE, "logo": DEFAULT_LOGO}


def get_brand(db: Session) -> dict:
    row = db.query(Brand).order_by(Brand.id).first()
    if row is None:
        return _default_payload()
    return {
        "id": row.id,
        "name": row.name or DEFAULT_NAME,
        "subtitle": row.subtitle,
        "logo": row.logo or DEFAULT_LOGO,
    }


def update_brand(db: Session, data: dict) -> dict:
    logo = data.get("logo")
    if logo is not None:
        if logo and not logo.startswith("data:image/"):
            raise BrandError("Logo 必须是图片（data URL）")
        if logo and len(logo.encode("utf-8")) > MAX_LOGO_BYTES * 4 // 3:
            raise BrandError("Logo 过大，请控制在 500KB 以内")

    row = db.query(Brand).order_by(Brand.id).first()
    if row is None:
        row = Brand(name=DEFAULT_NAME, subtitle=DEFAULT_SUBTITLE, logo="")
        db.add(row)
    if "name" in data and data["name"] is not None:
        row.name = data["name"].strip()[:64]
    if "subtitle" in data and data["subtitle"] is not None:
        row.subtitle = data["subtitle"].strip()[:128]
    if logo is not None:
        row.logo = "" if logo == DEFAULT_LOGO else logo
    db.commit()
    db.refresh(row)
    return get_brand(db)


def reset_brand(db: Session) -> dict:
    row = db.query(Brand).order_by(Brand.id).first()
    if row is not None:
        row.name = DEFAULT_NAME
        row.subtitle = DEFAULT_SUBTITLE
        row.logo = ""
        db.commit()
    return get_brand(db)
