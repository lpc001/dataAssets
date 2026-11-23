# -*- coding: utf-8 -*-
"""品牌定制：Logo 与系统名称。"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class Brand(Base):
    __tablename__ = "sys_brand"
    __table_args__ = {"comment": "系统品牌（Logo 与名称，单行配置）"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    name: Mapped[str] = mapped_column(String(64), nullable=False, default="", comment="系统名称（如 水投·指标平台）")
    subtitle: Mapped[str] = mapped_column(String(128), nullable=False, default="", comment="副标题/登录页说明")
    logo: Mapped[str] = mapped_column(
        Text, nullable=False, default="", comment="Logo 图片（base64 data URL，空=用内置默认）"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间"
    )
