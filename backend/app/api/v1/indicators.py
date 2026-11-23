import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.asset import Asset
from app.models.asset_column import AssetColumn
from app.models.caliber import Caliber
from app.models.governance_rule import GovernanceRule
from app.models.datasource import DataSource
from app.models.indicator import Indicator
from app.models.indicator_dimension import IndicatorDimension
from app.models.indicator_join import IndicatorJoin
from app.models.indicator_version import IndicatorVersion
from app.models.resource_column import ResourceColumn
from app.models.resource_table import ResourceTable
from app.models.user import User
from app.schemas.indicator import (
    AggregatePreviewIn,
    AggregatePreviewOut,
    CaliberCreate,
    JoinOut,
    CaliberOut,
    CaliberUpdate,
    IndicatorCreate,
    IndicatorDetail,
    IndicatorOut,
    IndicatorPage,
    IndicatorUpdate,
    DimensionOut,
    PathOut,
    RuleOut,
    ValidationSummary,
)
from app.services.indicator_preview import aggregate_preview
from app.services.indicator_validation import enabled_rules, summarize, validate_indicator
from app.services.permissions import require_perm

router = APIRouter(tags=["指标中心"])

DOMAIN_PREFIX = {"mkt": "BM", "svc": "BM"}
CYCLE_BY_GRAIN = {"YEAR": "年", "QUARTER": "季", "MONTH": "月", "DAY": "日"}


def _path(db: Session, column_id: int | None) -> PathOut | None:
    if not column_id:
        return None
    column = db.get(AssetColumn, column_id)
    if column is None:
        return None
    asset = db.get(Asset, column.asset_id)
    if asset is None:
        return None
    resource = db.get(ResourceTable, asset.resource_table_id)
    rc = db.get(ResourceColumn, column.resource_column_id)
    if resource is None:
        return None
    return PathOut(
        asset_id=asset.id,
        asset_name=asset.asset_name,
        schema_name=resource.schema_name,
        table_name=resource.table_name,
        column_name=column.column_name,
        data_type=rc.data_type if rc else None,
        domain_code=asset.domain_code,
    )


def _dimension_type(data_type: str | None) -> str:
    dtype = (data_type or "").lower()
    return "TIME" if ("date" in dtype or "time" in dtype) else "CATEGORY"


def _dimensions_out(db: Session, indicator_id: int) -> list[DimensionOut]:
    rows = db.scalars(
        select(IndicatorDimension)
        .where(IndicatorDimension.indicator_id == indicator_id)
        .order_by(IndicatorDimension.sort)
    ).all()
    result = []
    for dim in rows:
        column = db.get(AssetColumn, dim.asset_column_id)
        rc = db.get(ResourceColumn, column.resource_column_id) if column else None
        result.append(
            DimensionOut(
                id=dim.id,
                asset_column_id=dim.asset_column_id,
                column_name=column.column_name if column else "",
                data_type=rc.data_type if rc else None,
                dimension_type=dim.dimension_type,
                time_grain=dim.time_grain,
                alias=dim.alias,
            )
        )
    return result


def _joins_out(db: Session, indicator_id: int) -> list[JoinOut]:
    rows = db.scalars(
        select(IndicatorJoin).where(IndicatorJoin.indicator_id == indicator_id).order_by(IndicatorJoin.sort)
    ).all()
    result = []
    for join in rows:
        asset = db.get(Asset, join.asset_id)
        left = db.get(AssetColumn, join.left_asset_column_id)
        right = db.get(AssetColumn, join.right_asset_column_id)
        result.append(
            JoinOut(
                id=join.id,
                asset_id=join.asset_id,
                asset_name=asset.asset_name if asset else "",
                left_column_name=left.column_name if left else "",
                right_column_name=right.column_name if right else "",
                join_type=join.join_type,
            )
        )
    return result


def _next_code(db: Session, domain_code: str | None) -> str:
    prefix = DOMAIN_PREFIX.get(domain_code or "", "IN")
    rows = db.scalars(
        select(Indicator.indicator_code).where(Indicator.indicator_code.like(f"{prefix}%"))
    ).all()
    numbers = [int(r[len(prefix):]) for r in rows if r[len(prefix):].isdigit()]
    return f"{prefix}{(max(numbers) if numbers else 0) + 1:05d}"


def _record(db: Session, obj_type: str, obj_id: int, user: User, changes: dict, comment: str) -> None:
    last = db.scalar(
        select(func.max(IndicatorVersion.version_no)).where(
            IndicatorVersion.object_type == obj_type, IndicatorVersion.object_id == obj_id
        )
    ) or 0
    db.add(
        IndicatorVersion(
            object_type=obj_type,
            object_id=obj_id,
            version_no=int(last) + 1,
            changed_by=user.username,
            changed_at=datetime.now(),
            changes=json.dumps(changes, ensure_ascii=False),
            comment=comment,
        )
    )


def _to_out(db: Session, indicator: Indicator, rules: set[str]) -> IndicatorOut:
    issues = validate_indicator(db, indicator, rules)
    summary = summarize(issues)
    return IndicatorOut(
        id=indicator.id,
        indicator_code=indicator.indicator_code,
        indicator_name=indicator.indicator_name,
        domain_code=indicator.domain_code,
        status=indicator.status,
        unit=indicator.unit,
        cycle=indicator.cycle,
        owner_name=indicator.owner_name,
        source_path=_path(db, indicator.source_asset_column_id),
        carry_path=_path(db, indicator.carry_asset_column_id),
        aggregation=indicator.aggregation or "SUM",
        dimensions=_dimensions_out(db, indicator.id),
        joins=_joins_out(db, indicator.id),
        validation=ValidationSummary(block=summary["block"], warn=summary["warn"]),
    )


@router.get("/indicators", response_model=IndicatorPage)
def list_indicators(
    domain_code: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:indicator")),
):
    stmt = select(Indicator)
    if domain_code:
        stmt = stmt.where(Indicator.domain_code == domain_code)
    if status:
        stmt = stmt.where(Indicator.status == status)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(Indicator.indicator_code.ilike(like), Indicator.indicator_name.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Indicator.domain_code, Indicator.indicator_code).offset((page - 1) * page_size).limit(page_size)
    ).all()
    rules = enabled_rules(db)
    return IndicatorPage(items=[_to_out(db, r, rules) for r in rows], total=int(total))


@router.post("/indicators/preview", response_model=AggregatePreviewOut)
def preview_indicator(
    payload: AggregatePreviewIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:indicator")),
):
    asset = db.get(Asset, payload.asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="资产不存在")
    resource = db.get(ResourceTable, asset.resource_table_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="来源资源表不存在")
    datasource = db.get(DataSource, resource.datasource_id)
    if datasource is None:
        raise HTTPException(status_code=404, detail="数据源不存在")

    alias_map = {asset.id: "t0"}
    join_specs = []
    for index, join in enumerate(payload.joins, start=1):
        join_asset = db.get(Asset, join.asset_id)
        if join_asset is None:
            raise HTTPException(status_code=400, detail="关联资产不存在")
        join_resource = db.get(ResourceTable, join_asset.resource_table_id)
        if join_resource is None:
            raise HTTPException(status_code=400, detail="关联资产来源表不存在")
        if join_resource.datasource_id != resource.datasource_id:
            raise HTTPException(status_code=400, detail="关联资产必须与主资产同一数据源")
        left = db.get(AssetColumn, join.left_asset_column_id)
        right = db.get(AssetColumn, join.right_asset_column_id)
        if left is None or left.asset_id != asset.id:
            raise HTTPException(status_code=400, detail="主表关联字段不属于主资产")
        if right is None or right.asset_id != join.asset_id:
            raise HTTPException(status_code=400, detail="关联表关联字段不属于关联资产")
        alias = f"t{index}"
        alias_map[join.asset_id] = alias
        join_specs.append(
            {
                "alias": alias,
                "schema": join_resource.schema_name,
                "table": join_resource.table_name,
                "left_column": left.column_name,
                "right_column": right.column_name,
                "join_type": join.join_type,
            }
        )

    measure_name = None
    if payload.measure_asset_column_id:
        measure = db.get(AssetColumn, payload.measure_asset_column_id)
        if measure is None or measure.asset_id != asset.id:
            raise HTTPException(status_code=400, detail="度量字段必须来自主资产")
        measure_name = measure.column_name

    dims = []
    labels = []
    for dim in payload.dimensions:
        column = db.get(AssetColumn, dim.asset_column_id)
        if column is None or column.asset_id not in alias_map:
            raise HTTPException(status_code=400, detail="维度字段需来自主资产或已关联资产")
        rc = db.get(ResourceColumn, column.resource_column_id)
        dim_type = _dimension_type(rc.data_type if rc else None)
        if dim_type == "TIME" and not dim.time_grain:
            raise HTTPException(status_code=400, detail="时间维度必须选择时间粒度")
        name = (
            column.column_name
            if dim_type != "TIME"
            else f"{column.column_name}_{(dim.time_grain or '').lower()}"
        )
        dims.append(
            {
                "alias": alias_map[column.asset_id],
                "column": column.column_name,
                "time_grain": dim.time_grain if dim_type == "TIME" else None,
                "name": name,
            }
        )
        labels.append(name)

    try:
        columns, rows = aggregate_preview(
            datasource,
            resource.schema_name,
            resource.table_name,
            measure_name,
            payload.aggregation,
            dims,
            joins=join_specs,
            limit=20,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"预览失败：{exc.__class__.__name__}") from exc

    measure_hint = f"{payload.aggregation}({measure_name})" if measure_name else "count(*)"
    hint = f"{measure_hint}" + (f" 按 {', '.join(labels)}" if labels else "")
    return AggregatePreviewOut(columns=columns, rows=rows, hint=hint)


@router.get("/indicators/{indicator_id}", response_model=IndicatorDetail)
def get_indicator(
    indicator_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:indicator")),
):
    row = db.get(Indicator, indicator_id)
    if row is None:
        raise HTTPException(status_code=404, detail="指标不存在")
    rules = enabled_rules(db)
    base = _to_out(db, row, rules)
    issues = validate_indicator(db, row, rules)
    versions = db.scalars(
        select(IndicatorVersion)
        .where(IndicatorVersion.object_type == "INDICATOR", IndicatorVersion.object_id == row.id)
        .order_by(IndicatorVersion.version_no.desc())
    ).all()
    return IndicatorDetail(
        **base.model_dump(),
        theme=row.theme,
        indicator_level=row.indicator_level,
        indicator_type=row.indicator_type,
        indicator_def=row.indicator_def,
        formula=row.formula,
        caliber_id=row.caliber_id,
        carry_type=row.carry_type,
        source_type=row.source_type,
        created_at=row.created_at,
        updated_at=row.updated_at,
        issues=issues,
        versions=[
            {
                "version_no": v.version_no,
                "changed_by": v.changed_by,
                "changed_at": v.changed_at,
                "comment": v.comment,
            }
            for v in versions
        ],
    )


@router.post("/indicators", response_model=IndicatorDetail, status_code=201)
def create_indicator(
    payload: IndicatorCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:indicator")),
):
    column = db.get(AssetColumn, payload.source_asset_column_id)
    if column is None:
        raise HTTPException(status_code=400, detail="来源字段不存在")
    asset = db.get(Asset, column.asset_id)
    domain = payload.domain_code or (asset.domain_code if asset else None)
    column_asset_id = column.asset_id
    code = payload.indicator_code or _next_code(db, domain)
    if db.scalars(select(Indicator).where(Indicator.indicator_code == code)).first():
        raise HTTPException(status_code=409, detail="指标编码已存在")
    row = Indicator(
        **payload.model_dump(
            exclude={"indicator_code", "domain_code", "owner_name", "dimensions", "joins"}
        ),
        indicator_code=code,
        domain_code=domain,
        status="DRAFT",
        source_type="HUMAN",
        owner_name=payload.owner_name or user.username,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(row)
    db.flush()
    allowed_assets = {column_asset_id} | {j.asset_id for j in payload.joins}
    for index, dim in enumerate(payload.dimensions):
        column = db.get(AssetColumn, dim.asset_column_id)
        if column is None or column.asset_id not in allowed_assets:
            raise HTTPException(status_code=400, detail="维度字段需来自主资产或已关联资产")
        rc = db.get(ResourceColumn, column.resource_column_id)
        dim_type = _dimension_type(rc.data_type if rc else None)
        if dim_type == "TIME" and not dim.time_grain:
            raise HTTPException(status_code=400, detail="时间维度必须选择时间粒度")
        db.add(
            IndicatorDimension(
                indicator_id=row.id,
                asset_column_id=dim.asset_column_id,
                dimension_type=dim_type,
                time_grain=dim.time_grain if dim_type == "TIME" else None,
                sort=index,
            )
        )
    seen_assets = set()
    for index, join in enumerate(payload.joins):
        if join.asset_id in seen_assets or join.asset_id == column_asset_id:
            raise HTTPException(status_code=400, detail="关联资产重复")
        seen_assets.add(join.asset_id)
        join_asset = db.get(Asset, join.asset_id)
        if join_asset is None:
            raise HTTPException(status_code=400, detail="关联资产不存在")
        left = db.get(AssetColumn, join.left_asset_column_id)
        right = db.get(AssetColumn, join.right_asset_column_id)
        if left is None or left.asset_id != column_asset_id:
            raise HTTPException(status_code=400, detail="主表关联字段不属于主资产")
        if right is None or right.asset_id != join.asset_id:
            raise HTTPException(status_code=400, detail="关联表关联字段不属于关联资产")
        db.add(
            IndicatorJoin(
                indicator_id=row.id,
                asset_id=join.asset_id,
                left_asset_column_id=join.left_asset_column_id,
                right_asset_column_id=join.right_asset_column_id,
                join_type=join.join_type,
                sort=index,
            )
        )
    db.flush()
    time_dims = db.scalars(
        select(IndicatorDimension).where(
            IndicatorDimension.indicator_id == row.id,
            IndicatorDimension.dimension_type == "TIME",
        )
    ).all()
    if time_dims and time_dims[0].time_grain:
        row.cycle = CYCLE_BY_GRAIN.get(time_dims[0].time_grain, row.cycle)
    _record(db, "INDICATOR", row.id, user, {"action": "create"}, "创建指标")
    db.commit()
    db.refresh(row)
    rules = enabled_rules(db)
    base = _to_out(db, row, rules)
    return IndicatorDetail(
        **base.model_dump(),
        theme=row.theme,
        indicator_level=row.indicator_level,
        indicator_type=row.indicator_type,
        indicator_def=row.indicator_def,
        formula=row.formula,
        caliber_id=row.caliber_id,
        carry_type=row.carry_type,
        source_type=row.source_type,
        created_at=row.created_at,
        updated_at=row.updated_at,
        issues=validate_indicator(db, row, rules),
        versions=[],
    )


@router.patch("/indicators/{indicator_id}", response_model=IndicatorDetail)
def update_indicator(
    indicator_id: int,
    payload: IndicatorUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:indicator")),
):
    row = db.get(Indicator, indicator_id)
    if row is None:
        raise HTTPException(status_code=404, detail="指标不存在")
    data = payload.model_dump(exclude_unset=True)
    changes: dict = {}
    dimensions = data.pop("dimensions", None)
    joins = data.pop("joins", None)
    if dimensions is not None:
        from sqlalchemy import delete as sql_delete

        source = db.get(AssetColumn, row.source_asset_column_id) if row.source_asset_column_id else None
        main_asset_id = source.asset_id if source else None
        if joins is not None:
            allowed = {main_asset_id} | {j["asset_id"] for j in joins}
        else:
            allowed = {main_asset_id} | set(
                db.scalars(
                    select(IndicatorJoin.asset_id).where(IndicatorJoin.indicator_id == row.id)
                ).all()
            )
        db.execute(sql_delete(IndicatorDimension).where(IndicatorDimension.indicator_id == row.id))
        for index, dim in enumerate(dimensions):
            column = db.get(AssetColumn, dim["asset_column_id"])
            if column is None or column.asset_id not in allowed:
                raise HTTPException(status_code=400, detail="维度字段需来自主资产或已关联资产")
            rc = db.get(ResourceColumn, column.resource_column_id)
            dim_type = _dimension_type(rc.data_type if rc else None)
            if dim_type == "TIME" and not dim.get("time_grain"):
                raise HTTPException(status_code=400, detail="时间维度必须选择时间粒度")
            db.add(
                IndicatorDimension(
                    indicator_id=row.id,
                    asset_column_id=dim["asset_column_id"],
                    dimension_type=dim_type,
                    time_grain=dim.get("time_grain") if dim_type == "TIME" else None,
                    sort=index,
                )
            )
        time_dim = next((d for d in dimensions if d.get("time_grain")), None)
        if time_dim:
            row.cycle = CYCLE_BY_GRAIN.get(time_dim["time_grain"], row.cycle)
        changes["dimensions"] = {"new": len(dimensions)}
    if joins is not None:
        from sqlalchemy import delete as sql_delete

        db.execute(sql_delete(IndicatorJoin).where(IndicatorJoin.indicator_id == row.id))
        for index, join in enumerate(joins):
            db.add(
                IndicatorJoin(
                    indicator_id=row.id,
                    asset_id=join["asset_id"],
                    left_asset_column_id=join["left_asset_column_id"],
                    right_asset_column_id=join["right_asset_column_id"],
                    join_type=join.get("join_type", "LEFT"),
                    sort=index,
                )
            )
        changes["joins"] = {"new": len(joins)}
    for key, value in data.items():
        old = getattr(row, key)
        if old != value:
            changes[key] = {"old": old, "new": value}
            setattr(row, key, value)
    if row.status == "PUBLISHED":
        row.status = "DRAFT"
    row.updated_at = datetime.now()
    if changes:
        _record(db, "INDICATOR", row.id, user, changes, "修改指标")
    db.commit()
    db.refresh(row)
    return get_indicator(indicator_id, db, user)


@router.post("/indicators/{indicator_id}/publish", response_model=IndicatorDetail)
def publish_indicator(
    indicator_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:indicator")),
):
    row = db.get(Indicator, indicator_id)
    if row is None:
        raise HTTPException(status_code=404, detail="指标不存在")
    rules = enabled_rules(db)
    summary = summarize(validate_indicator(db, row, rules))
    if summary["block"]:
        raise HTTPException(status_code=409, detail={"message": "存在阻断问题，不能发布", "issues": summary["issues"]})
    row.status = "PUBLISHED"
    row.updated_at = datetime.now()
    _record(db, "INDICATOR", row.id, user, {"status": "PUBLISHED"}, "发布指标")
    db.commit()
    return get_indicator(indicator_id, db, user)


@router.post("/indicators/{indicator_id}/retire", response_model=IndicatorDetail)
def retire_indicator(
    indicator_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:indicator")),
):
    row = db.get(Indicator, indicator_id)
    if row is None:
        raise HTTPException(status_code=404, detail="指标不存在")
    row.status = "RETIRED"
    row.updated_at = datetime.now()
    _record(db, "INDICATOR", row.id, user, {"status": "RETIRED"}, "废止指标")
    db.commit()
    return get_indicator(indicator_id, db, user)


@router.get("/calibers", response_model=list[CaliberOut])
def list_calibers(
    kind: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:indicator")),
):
    stmt = select(Caliber)
    if kind:
        stmt = stmt.where(Caliber.caliber_kind == kind)
    return list(db.scalars(stmt.order_by(Caliber.caliber_code)).all())


@router.post("/calibers", response_model=CaliberOut, status_code=201)
def create_caliber(
    payload: CaliberCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:indicator")),
):
    if db.scalars(select(Caliber).where(Caliber.caliber_code == payload.caliber_code)).first():
        raise HTTPException(status_code=409, detail="口径编码已存在")
    row = Caliber(
        **payload.model_dump(),
        status="DRAFT",
        source_type="HUMAN",
        owner_name=user.username,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/calibers/{caliber_id}", response_model=CaliberOut)
def update_caliber(
    caliber_id: int,
    payload: CaliberUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:indicator")),
):
    row = db.get(Caliber, caliber_id)
    if row is None:
        raise HTTPException(status_code=404, detail="口径不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    row.updated_at = datetime.now()
    db.commit()
    db.refresh(row)
    return row


@router.get("/governance-rules", response_model=list[RuleOut])
def list_rules(
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("ast:indicator")),
):
    return list(db.scalars(select(GovernanceRule).order_by(GovernanceRule.rule_code)).all())
