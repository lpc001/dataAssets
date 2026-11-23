# 指标中心设计方案（v1.2 · 资产驱动 · 台账落平台库）

- 版本：v1.2
- 日期：2026-11-23
- 变更：台账不再回写 `water_dw`（模拟中间层，只读不写）；`dim_indicator` / `dim_caliber_dict` 落在平台库 `data_assets`；补充「指标取数路径」设计。

---

## 1. 定位

- **平台库 `data_assets` 是指标与口径的唯一源头**；
- `water_dw` 是模拟出来的中间输出层，**只读、绝不写入**；
- 对外的 `dim_indicator` / `dim_caliber_dict` 以**视图**形式建在 `data_assets` 内，下游直接读平台库，无需回写、无需写账号。

```text
资产字段（data_assets 内登记）
      │ ① 选数据域 → 选该域资产字段 → 创建指标
      ▼
  指标草稿（定义/公式/单位/周期/口径）
      │ ② 校验（引用完整性 / 公式 / 域一致性）
      ▼
  发布（平台指标目录）
      ▼
  data_assets 视图：dim_indicator / dim_caliber_dict（下游直接读）
```

## 2. 已确认决策

| 决策 | 结论 |
|---|---|
| 审批流 | 不做，校验门禁 + 人工确认 |
| 存量台账 | 一次性迁移为草稿，不是日常入口 |
| 指标与口径 | 一对一（`caliber_id` 外键，不建中间表） |
| 流程起点 | 数据资产字段 |
| 台账存放 | `data_assets`（视图），**不写 `water_dw`** |

## 3. 主流程（日常）

1. 资产目录 → 选择**数据域** → 进入该域下的资产 → 字段 → 「创建指标」；
2. 来源字段自动带出（不可手填），并**自动解析取数路径**；
3. 填写名称、编码、定义、单位、周期、公式；
4. 新建或关联口径（一对一）；
5. 校验：阻断项清零才能发布；
6. 发布：进入指标目录；`data_assets.cdm.dim_indicator` 视图实时可见；
7. 变更：修改已发布指标 → 退回草稿重审 → 再发布，全程留版本。

### 3.1 取数路径（本次新增，重点）

指标维护在平台库，但要能回答"这个指标的数据从哪个域、哪张表、哪个字段取"。解析链：

```text
指标.domain_code
  └─ source_asset_column_id → 资产字段
       └─ asset → resource_table（schema.table）
            └─ datasource（主机/库/只读账号）
```

规则：

- 创建指标时**先选数据域**，字段选择器只列该域下已登记资产的字段，避免跨域误挂；
- 指标详情固定展示「取数路径」：数据域 → 数据源 → `schema.表.字段`，并可直接打开该字段所在资产的数据预览；
- 校验规则 R11：指标归属域必须与来源字段所属资产的域一致（不一致阻断）；
- 一个指标只允许一个来源字段（一对一取数），跨表派生走公式里的字段引用，不另挂来源。

## 4. 数据模型

### 4.1 `ast_indicator`

indicator_code / indicator_name / **domain_code** / theme / indicator_level / indicator_type / indicator_def / formula / unit / cycle / **source_asset_column_id** / **carry_asset_column_id** / carry_type / **caliber_id** / status（DRAFT/PUBLISHED/RETIRED）/ source_type（HUMAN/AI/IMPORT）/ owner_name / created_at / updated_at。

### 4.2 `ast_caliber`

caliber_code / caliber_name / caliber_def / formula / source_fields / value_type / apply_layer / **caliber_kind**（INDICATOR/ENUM/SLA）/ status / source_type / owner_name。

### 4.3 `ast_governance_rule`

rule_code / rule_name / target / severity（BLOCK/WARN）/ params(JSON) / enabled / description。

### 4.4 `ast_indicator_version`

object_type / object_id / version_no / changed_by / changed_at / changes(JSON)。

### 4.5 对外台账视图（data_assets）

```sql
create schema if not exists cdm;
create or replace view cdm.dim_indicator as
select indicator_code, indicator_name, domain_code, indicator_def, formula, unit, cycle,
       caliber_code_snapshot, ... from ast_indicator where status = 'PUBLISHED';
-- dim_caliber_dict 同理
```

下游把连接从 `water_dw` 切到 `data_assets` 即可，数据实时、无同步任务。

## 5. 校验规则

| 编码 | 规则 | 级别 |
|---|---|---|
| R01 | 必填完整 | 阻断 |
| R02 | 编码唯一且符合主题码规范 | 阻断 |
| R03 | 来源字段必须来自已登记资产字段 | 阻断 |
| R04 | 承载字段存在且为数值型 | 阻断 |
| R05 | 公式可解析，非自然语言 | 阻断 |
| R06 | 必须关联口径 | 警告 |
| R07 | 同域内名称不重复 | 警告 |
| R08 | 暂缓/跨域指标不得挂承载字段 | 警告 |
| R09 | 单位/周期与类型匹配 | 警告 |
| R10 | 已发布指标必须有责任人 | 警告 |
| **R11** | **指标归属域与来源字段所属资产的域一致** | 阻断 |

## 6. 存量迁移（一次性）

读 `water_dw` 的 `dim_indicator`（53）与 `dim_caliber_dict`（38）→ 按前缀拆口径三类 → 解析字段映射（实测 36 项可挂、17 项失败）→ 全部落草稿 → 人工补挂后发布。

## 7. 界面

| 页面 | 内容 |
|---|---|
| 资产目录 · 字段 | 「创建指标」入口（预填域与来源字段） |
| 指标中心 | 列表（编码/名称/域/状态/校验/取数路径/口径） |
| 指标详情 | 表单、**取数路径面板**、校验结果、版本历史、预览入口 |
| 口径管理 | 三类分组、关联指标、编辑 |
| 规则管理 | 开关与级别 |
| 台账视图 | 展示 `data_assets.cdm` 视图定义与下游连接说明 |

## 8. 分期

| 阶段 | 内容 |
|---|---|
| I1 | 指标/口径/规则/版本表；按域选字段创建指标；取数路径；校验；列表/详情 |
| I2 | 口径管理、发布门禁、版本历史、台账视图 |
| I3 | 存量迁移工具、指标健康巡检、下游接入说明 |

## 9. 风险

- 视图字段需与下游预期对齐，字段名变更要同步通知；
- 指标与资产字段强绑定，资产字段下线会导致指标阻断（这是预期行为，需在资产下线时提示影响）；
- 存量 17 项需人工补挂，属一次性成本。

---

本文件由水务加出品的 WaterPlusAI 辅助编制，资料来源以文中标注为准。本文件供内部研讨参考，正式决策请以权威文件和内部数据为准。
