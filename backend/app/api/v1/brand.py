# -*- coding: utf-8 -*-
"""品牌配置：读取（公开）与更新（需系统管理权限）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.brand import BrandRead, BrandUpdate
from app.services import brand as brand_svc
from app.services.permissions import require_perm

public_router = APIRouter(prefix="/brand", tags=["brand"])
admin_router = APIRouter(
    prefix="/brand",
    tags=["brand"],
    dependencies=[Depends(get_current_user), Depends(require_perm("system:brand"))],
)


@public_router.get("", response_model=BrandRead)
def get_brand(db: Session = Depends(get_db)):
    """品牌配置（登录页也要用，故不要求登录）。"""
    return brand_svc.get_brand(db)


@admin_router.put("", response_model=BrandRead)
def update_brand(data: BrandUpdate, db: Session = Depends(get_db)):
    try:
        return brand_svc.update_brand(db, data.model_dump(exclude_unset=True))
    except brand_svc.BrandError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@admin_router.post("/reset", response_model=BrandRead)
def reset_brand(db: Session = Depends(get_db)):
    """恢复默认品牌。"""
    return brand_svc.reset_brand(db)
