# 水务高质量数据集 · 数据资产管理平台设计方案

- 版本：v1.0（定稿）
- 日期：2026-11-23
- 代码目录：`E:\AI工具\资产目录管理平台`
- 基础框架：FastAPI + SQLAlchemy 2.x + Pydantic v2 + PostgreSQL（后端）／Vue 3 + TypeScript + Vite + Element Plus + Pinia（前端）
- 平台库：PostgreSQL `localhost:5432 / data_assets`
- 关联文档：《项目进度与待办.md》《规范_数据域切分判断标准.md》《规范_敏感数据最小化原则.md》《客户与营销域数据模型打样_V2.md》《客户服务域数据模型打样_V1.md》

---

## 1. 背景

「水务高质量数据集」目前是一套水务行业标准 CDM 数据模型的打样成果 + 一套可复算的 Mock 数据 + 一套治理规范：

| 资产 | 现状 |
|---|---|
| 数据域 | 10 域固定规划，已打样 2 域（mkt 客户与营销、svc 客户服务），其余 8 域未打样 |
| 表 | 36 张（mkt 29 + svc 7），`water_dw` 中 `cdm` 与 `cdm_mock` 双 schema 结构一致 |
| 指标 | `dim_indicator` 53 项（营销 16 + 客服 37） |
| 口径 | `dim_caliber_dict` 38 条（营销 12 + 客服 26） |
| 数据量 | 营销域约 3.7 万明细 + 1.2 万汇总；客服域 4.05 万明细 + 778 汇总；期间 2026-01-01～2026-12-31 |
| 质量证据 | 营销域 6 组 37 项、客服域 6 组 65 项检查全部通过；两份《指标实测值对照表》 |
| 规范 | 《数据域切分判断标准》《敏感数据最小化原则》均定稿 |
| 工程资产 | 45 个 Python 脚本、3 份 SQL；目录无 git 仓库，脚本平铺 |

现状的问题是：模型、指标、口径、规范、验证结论散落在 Markdown 与脚本里，没有可检索、可关联、可追溯的载体。本平台把这些内容资产化。

## 2. 目标与非目标

### 2.1 目标（一期）

1. **数据源配置**：平台可配置多个只读数据源，从目标库读取元数据；
2. **资产目录**：域 → 业务过程 → 表 → 字段四级目录，带中文名、注释、分层、追溯档、敏感级别等治理属性；
3. **指标中心**：53 项指标、38 条口径入库，指标可挂到承载字段，形成追溯链路；
4. **数据预览**：表数据只读预览，敏感字段按级别脱敏，全程审计；
5. **血缘图**：表级/字段级血缘，人工登记为主、规则推导候选为辅，图形化展示；
6. **规范中心**：规范条款化，可挂载到表/字段/指标，可执行合规检查。

### 2.2 非目标（一期不做）

- 不纳管原始资料（指标卡/模型成果 xlsx 等设计输入材料）；
- 不做 ADS 层与报表/大屏；
- 不做数据加工调度与 ETL 执行；
- 不做自动质量跑批（一期只做规范合规检查，数据质量验证结论以文档/规则登记体现）；
- 不做多租户。

## 3. 技术决策（已确认）

| 决策 | 结论 |
|---|---|
| 目标库适配 | 一期只做 PostgreSQL；数据源适配以 `DataSourceAdapter` 接口抽象，后续可扩 MySQL/Hive |
| 目录归类 | 按表命名规则自动归域/分层，人工可修正 |
| 血缘来源 | 人工登记 + 规则推导候选（候选需人工确认） |
| 预览脱敏 | 按字段 `sensitive_level` 逐字段处理：L1 明文、L2/L3 掩码；另设 `ast:preview:raw` 权限点查看明文并强制审计 |

## 4. 总体架构

```text
┌──────────────────────────── 数据资产管理平台（data_assets） ────────────────────────────┐
│ 系统管理（组织/用户/角色/品牌）                                                          │
│ 数据源管理 ── 只读连接 ──▶ 目标库 water_dw（cdm / cdm_mock）                             │
│ 资产目录（域→业务过程→表→字段）  ← 元数据同步                                            │
│ 指标中心（指标/口径/承载映射/追溯）                                                      │
│ 数据预览（只读 + 脱敏 + 审计）  ── 直连目标库查询                                        │
│ 血缘图（表级/字段级）                                                                    │
│ 规范中心（条款 + 挂载 + 合规检查）                                                       │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

原则：**资产目录落在平台自有库**，目标库只读。同步只拉结构与注释；标注、指标、血缘、规范、审计全部存平台侧。目标库不可用时，目录仍可浏览。

## 5. 对象模型

```text
数据源 DataSource
  └─ 表 Table ── 字段 Column
       ├─ 归属：数据域 Domain（10 个内置）→ 业务过程 Subject
       ├─ 血缘：Lineage（起点表.字段 → 终点表.字段）
       ├─ 指标：Indicator ── 承载映射 IndicatorMap ──▶ 表.字段
       ├─ 口径：Caliber（可被指标引用、可被字段引用）
       └─ 规范：StandardClause（经 StandardLink 挂载）
```

## 6. 数据模型

新增 13 张表，统一 `ast_` 前缀，主键沿用框架 `BigIntPK`，所有表与字段带 COMMENT。

### 6.1 `ast_datasource` 数据源

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint PK | |
| name | varchar(64) | 数据源名称，唯一 |
| db_type | varchar(16) | 数据库类型，一期固定 `postgresql` |
| host / port | varchar(128) / int | 连接地址 |
| database_name | varchar(64) | 库名 |
| schema_filter | varchar(255) | 采集的 schema，逗号分隔，如 `cdm,cdm_mock` |
| username | varchar(64) | 只读账号 |
| password_cipher | text | 密码密文（Fernet，密钥由 SECRET_KEY 派生） |
| readonly_verified | boolean | 只读校验是否通过 |
| last_sync_at | timestamp | 最后同步时间 |
| status | varchar(16) | 启用/停用 |
| remark | varchar(255) | |

### 6.2 `ast_sync_log` 同步日志

数据源、开始/结束时间、状态、新增/变更/消失的表数与字段数、错误信息、操作人。

### 6.3 `ast_domain` 数据域（10 条内置）

| 字段 | 说明 |
|---|---|
| domain_code | 域码：mkt/prd/net/dsp/wqm/svc/ast/drn/prj/she |
| domain_name | 中文名 |
| sampled | 是否已打样（当前 mkt、svc 为 true） |
| sort | 排序 |
| description | 边界说明（取自规范） |

### 6.4 `ast_subject` 业务过程

所属域、名称、说明、排序。例：mkt 域下的报装、抄表、计费、收费、欠费、表务、营业变更。

### 6.5 `ast_table` 表资产

| 字段 | 说明 |
|---|---|
| datasource_id | FK → ast_datasource |
| schema_name / table_name | 远端定位；唯一键 (datasource_id, schema_name, table_name) |
| table_comment | 远端表注释 |
| business_name | 业务中文名（可覆盖注释） |
| layer | DIM / DWD / DWS |
| domain_code | 所属域（可空=公共维度） |
| subject_id | 所属业务过程（可空） |
| owner_domain_code | 主责域（如 dim_cust 主责营销域） |
| trace_level | 追溯档 A/B/C/D |
| partition_field | 分区字段（通常 ds） |
| is_scd2 | 是否 SCD2 慢变维 |
| row_count | 最近同步行数 |
| remote_status | ACTIVE / MISSING（远端已消失） |
| remark | |

### 6.6 `ast_column` 字段资产

所属表、字段名、序号、数据类型、是否可空、默认值、是否主键、字段注释、业务含义、是否分区键、敏感级别（L1/L2/L3）、口径编码、远端状态。唯一键 (table_id, column_name)。

### 6.7 `ast_indicator` 指标

编码（唯一）、名称、定义、公式、单位、累计周期、分析层级、主题、类型（原子/衍生）、状态（已映射/暂缓/跨域/外部基数）、来源表字段、备注。

### 6.8 `ast_caliber` 口径

口径编码（唯一）、名称、定义、公式、来源字段、取值类型（标准/可配置）、适用层级、关联指标编码、备注。

### 6.9 `ast_indicator_map` 指标承载映射

指标 → (表, 字段)、承载方式（DWS 固定列/明细现算/配置项）、说明。一个指标可多条（如从 DWS 与明细两条路径都可追溯）。

### 6.10 `ast_lineage` 血缘边

起点 (table_id, column_name) → 终点 (table_id, column_name)、转换说明、来源（MANUAL/RULE）、规则编码、确认状态（候选/已确认）、操作人。

### 6.11 `ast_standard` / `ast_standard_clause` 规范与条款

规范：名称、版本、状态（定稿/草稿）、来源文件。
条款：所属规范、条款编号、标题、正文、类别（建模/命名/敏感数据/质量）、排序。

### 6.12 `ast_standard_link` 规范挂载

条款 → 对象类型（TABLE/COLUMN/INDICATOR/DATASOURCE）+ 对象 ID、检查结果（通过/不符/未检查）、说明。

### 6.13 `ast_preview_audit` 预览审计

用户、数据源、表、查询条件、返回行数、是否请求明文、IP、时间。

## 7. 元数据同步

### 7.1 数据源安全

- 密码写入即加密，接口永不回显，前端只显示"已配置"；
- 保存前执行只读校验：`select 1` + 查询 `pg_roles` 确认非超级用户；写权限检测失败则标记 `readonly_verified=false` 并提示；
- 连接串由后端拼装，前端不接触凭据。

### 7.2 元数据采集（PostgreSQL）

- 表：`information_schema.tables`（限定 schema_filter 中的 schema，排除视图）；
- 表注释：`pg_catalog.obj_description(oid,'pg_class')`；
- 字段：`information_schema.columns` + `col_description(oid, ordinal)`；
- 主键：`information_schema.table_constraints` + `key_column_usage`；
- 行数：`pg_stat_user_tables.n_live_tup` 估算，或大表用精确 count（配置开关）。

### 7.3 同步算法

1. 拉取远端元数据快照；
2. 按唯一键与平台已有记录比对：新增 → 插入；存在 → 更新结构字段（不覆盖人工标注）；远端消失 → 标记 `remote_status=MISSING`；
3. 写入同步日志（新增/变更/消失计数）；
4. 同步幂等：重复执行不产生重复记录，人工标注（business_name、domain_code、trace_level、敏感级别）不被覆盖。

### 7.4 漂移识别

每次同步产出差异清单：新增表/字段、类型变更、注释变更、远端消失。在数据源详情页展示最近一次差异。

## 8. 目录与业务标注

### 8.1 自动归类规则

| 规则 | 结果 |
|---|---|
| `^dim_` | 层=DIM，域=公共维度（domain_code 空） |
| `^dwd_([a-z]{3})_` | 层=DWD，域=捕获的域码 |
| `^dws_([a-z]{3})_` | 层=DWS，域=捕获的域码 |
| `^dws_nrw_` | 跨域专题，域=空 |
| 表名 `dim_cust`/`dim_meter` | 公共维度，主责域=mkt |

自动归类只在表首次入库时执行，人工修改后不再覆盖。

### 8.2 待标注清单

以下情况进入"待标注"视图：缺中文名、缺所属域、DWD/DWS 缺追溯档、字段缺敏感级别。一期作为提示，不阻断。

### 8.3 表详情聚合

基本信息 / 字段清单 / 数据预览 / 血缘 / 关联指标 / 关联规范，六个 tab。

## 9. 指标与口径

### 9.1 导入

目标库存在 `dim_indicator`、`dim_caliber_dict` 时，同步过程顺带读取其数据作为初始指标/口径（字段映射在适配层配置）；也可手工新增。

### 9.2 承载映射

按 `dim_indicator.source_table_field`（形如 `表.字段`）解析生成 `ast_indicator_map`；解析失败进入"待挂载"清单。

### 9.3 追溯链路

指标 → 承载字段 → 血缘上游字段，逐级展开。与现有《营销域指标映射追溯表》《客户服务域指标实测值对照表》一一对应。

## 10. 数据预览

### 10.1 安全边界

- 只读账号连接；仅允许单条 SELECT；服务端强制 `LIMIT`（默认 100，上限 500）、`statement_timeout=10s`；
- 禁止 DDL/DML/多语句；
- 预览走独立连接池，与同步连接隔离。

### 10.2 脱敏规则

| 级别 | 处理 |
|---|---|
| L1 | 明文 |
| L2 | 掩码（保留首尾字符，中间打码）；数值类降精度 |
| L3 | 默认不展示（本数据集无此类字段） |

本数据集的 L2 字段基本不存在（证件/银行/电话/住址均未落库），实际预览绝大部分字段完整可见。

### 10.3 明文与审计

`ast:preview:raw` 权限可查看明文；每次预览（含普通预览）写 `ast_preview_audit`，明文查看额外标记。

## 11. 血缘

### 11.1 人工登记

选择起点/终点（表 + 字段，可批量），填写转换说明；落库为 `MANUAL`，状态"已确认"。

### 11.2 规则推导候选

| 规则编码 | 规则 | 生成的边 |
|---|---|---|
| R-DIM-01 | DWD 字段 `*_code` 与 DIM 同名字段 | dim.x → dwd.y |
| R-DWS-01 | DWS 字段与同域 DWD 同名字段 | dwd.x → dws.y |
| R-IND-01 | 指标承载映射的 (表.字段) 与来源表字段 | 来源字段 → 承载字段 |

候选写入 `ast_lineage`（来源 RULE、状态"候选"），人工确认后转"已确认"，可批量确认/驳回。

### 11.3 图展示

- 表级：按域分组的关系图，可下钻到字段级；
- 字段级：上下游分层展开（递归 CTE，限制深度 5）；
- 前端用 ECharts `graph` 类型渲染，支持缩放、拖拽、按域着色。

## 12. 规范中心

### 12.1 条款化

将两份规范拆为条款入库：条款编号、标题、正文、类别。后续规范按同结构追加。

### 12.2 挂载

条款可挂到表/字段/指标，记录检查结果。如"敏感数据最小化-条款一"挂到 `dim_cust` 的证件/电话类字段（若存在）。

### 12.3 合规检查（首批 6 条）

| 编码 | 规则 |
|---|---|
| C-01 | DWD/DWS 表必须有 ds 分区字段 |
| C-02 | 表必须有中文名 |
| C-03 | 字段必须有注释 |
| C-04 | L2/L3 字段不得出现在 DWS |
| C-05 | 指标必须挂载到至少一个承载字段（或标记暂缓/跨域/外部基数） |
| C-06 | 已打样域的表必须有追溯档 |

检查结果按表/域汇总，出"合规报告"页。

## 13. 权限与菜单

权限点（追加到 `core/permissions.py`）：

| 编码 | 名称 | 分组 |
|---|---|---|
| ast:datasource | 数据源管理 | 资产管理 |
| ast:catalog | 资产目录 | 资产管理 |
| ast:indicator | 指标中心 | 资产管理 |
| ast:lineage | 血缘 | 资产管理 |
| ast:preview | 数据预览 | 资产管理 |
| ast:preview:raw | 预览明文 | 资产管理 |
| ast:standard | 规范中心 | 资产管理 |

菜单：资产总览 / 数据源管理 / 资产目录 / 指标中心 / 规范中心 / 血缘图。

## 14. API 设计（`/api/v1` 下）

| 模块 | 端点 |
|---|---|
| 数据源 | `GET/POST /datasources`、`PUT/DELETE /datasources/{id}`、`POST /datasources/{id}/test`、`POST /datasources/{id}/sync`、`GET /datasources/{id}/sync-logs` |
| 目录 | `GET /domains`、`GET /subjects`、`GET /tables`（筛选：域/层/schema/关键字）、`GET /tables/{id}`、`PATCH /tables/{id}`、`GET /tables/{id}/columns`、`PATCH /columns/{id}` |
| 预览 | `POST /tables/{id}/preview`（body：offset/limit/字段）、`GET /preview-audits` |
| 指标 | `GET/POST /indicators`、`PUT /indicators/{id}`、`GET/POST /calibers`、`GET /indicators/{id}/lineage` |
| 血缘 | `GET/POST /lineage`、`POST /lineage/{id}/confirm`、`POST /lineage/derive`（生成候选）、`GET /lineage/graph?table_id=` |
| 规范 | `GET /standards`、`GET /clauses`、`POST /standard-links`、`POST /compliance/check`、`GET /compliance/report` |

## 15. 前端页面

| 页面 | 要点 |
|---|---|
| 资产总览 | 卡片：表数/字段数/指标数/规范条款数/漂移数；域分布图 |
| 数据源管理 | 列表 + 新建抽屉（连接表单、测试连接）+ 同步按钮 + 差异抽屉 |
| 资产目录 | 左侧域/过程树 + 右侧表列表 + 表详情六 tab |
| 指标中心 | 指标列表（状态筛选）+ 指标详情（口径、承载字段、追溯链） |
| 血缘图 | 画布 + 左侧筛选（域/表）+ 右侧详情；候选边虚线、已确认实线 |
| 规范中心 | 规范与条款树 + 挂载列表 + 合规报告 |

视觉沿用 `docs/设计规范.md`（清亮蓝主色 `#0A84FF`、冷白底 `#F5FAFF`、Element Plus 变量覆盖）。

## 16. 分期与验收

| 阶段 | 内容 | 验收标准 |
|---|---|---|
| P1 | 数据源配置、元数据同步、目录骨架 | 配置 water_dw 后一键同步出 2 schema、36 表、全部字段与注释；重复同步幂等；能报出漂移 |
| P2 | 业务标注、指标/口径中心 | 10 域归位；53 指标、38 口径入库；指标可挂承载字段并看到追溯链 |
| P3 | 数据预览 | 36 表可预览；L2 字段掩码；审计可查 |
| P4 | 血缘 | 人工可登记、规则可生成候选、图可渲染 |
| P5 | 规范中心 | 条款入库、可挂载、6 条检查可执行并出报告 |

## 17. 风险与待决

| 项 | 说明 | 应对 |
|---|---|---|
| 血缘人工成本 | 36 表、数百字段，全靠人工登记不现实 | 规则候选先铺底，人工只确认与补字段级细节 |
| 预览性能 | 明细表 1.7 万行，大表查询可能慢 | 强制 LIMIT + 超时；必要时只允许按分区字段过滤 |
| 目标库适配 | 一期仅 PG | 适配器接口预留 `get_tables/get_columns/quote_ident` |
| 标注维护 | 同步不覆盖人工标注，但字段类型变更会提示 | 用差异报告驱动人工复核 |
| 密码安全 | 平台持有目标库凭据 | 密文存储、接口不回显、只读账号、可随时停用数据源 |

---

## 18. v1.1 修订：资源池与资产两层（2026-11-23）

第一版把「技术元数据」和「业务资产」合并在一张 `ast_table` 里，采集即资产，缺少登记与维护环节，属于结果向设计。现修订为两层：

| 层 | 表 | 职责 |
|---|---|---|
| 资源池 | `ast_resource_table` / `ast_resource_column` | 采集落点；表/字段/注释/行数/远端状态；标识系统表与临时表；只给"建议归属"（规则推导），不承载业务语义 |
| 元数据版本 | `ast_meta_version` / `ast_meta_change` | 每次采集一个版本，逐项记录表/字段的 ADD/MODIFY/DROP、变化属性与前后值 |
| 资产 | `ast_asset` / `ast_asset_column` | 从资源池登记产生，1 资产 = 1 张资源表；承载域、业务过程、责任人、追溯档、状态（草稿/已发布/已下线）与字段业务标注 |

流程：数据源 → 采集 → 资源池（含待登记队列）→ 批量登记（规则预填、直接发布）→ 资产目录。

补充决策：
- 资源池全量收录，系统表/临时表只做标识，通过登记动作筛选；
- 字段业务标注（业务中文名、敏感级别、关键字段）落在资产层，采集不覆盖；
- 采集新增字段会同步追加到已登记资产的字段清单；
- 存量 72 张表一次性迁移为资源 + 已发布资产，目录视图保持不变；
- 原 `ast_table` / `ast_column` / `ast_sync_log` 已下线，对应关系见迁移脚本 `backend/scripts/migrate_two_layer.py`。

---

本文件由水务加出品的 WaterPlusAI 辅助编制，资料来源以文中标注为准。本文件供内部研讨参考，正式决策请以权威文件和内部数据为准。
