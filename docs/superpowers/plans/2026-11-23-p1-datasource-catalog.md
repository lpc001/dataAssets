# P1 数据源与资产目录 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让平台能配置数据源、从目标库同步元数据，并在目录中展示 域→业务过程→表→字段。

**Architecture:** 平台自有库 `data_assets` 存资产目录；`DataSourceAdapter` 抽象目标库读取；同步服务负责幂等 upsert 与漂移识别；前端以域树 + 表列表 + 表详情呈现。

**Tech Stack:** FastAPI / SQLAlchemy 2.x / Pydantic v2 / PostgreSQL / Vue 3 + Element Plus / pytest

---

## File Structure

| 文件 | 职责 |
|---|---|
| `backend/app/core/crypto.py` | 凭据加密（Fernet，密钥由 SECRET_KEY 派生） |
| `backend/app/adapters/base.py` | 远端元数据 DTO 与适配器协议 |
| `backend/app/adapters/postgres.py` | PostgreSQL 元数据读取（表/字段/注释/主键/行数） |
| `backend/app/models/datasource.py` | `ast_datasource` |
| `backend/app/models/sync_log.py` | `ast_sync_log` |
| `backend/app/models/domain.py` | `ast_domain`（10 域内置） |
| `backend/app/models/subject.py` | `ast_subject` |
| `backend/app/models/table_asset.py` | `ast_table` |
| `backend/app/models/column_asset.py` | `ast_column` |
| `backend/app/services/classify.py` | 命名规则归类（层/域/追溯档） |
| `backend/app/services/sync.py` | 同步编排、幂等 upsert、漂移计数 |
| `backend/app/schemas/datasource.py` / `catalog.py` | 请求/响应模型 |
| `backend/app/crud/datasource.py` / `table_asset.py` | 数据访问 |
| `backend/app/api/v1/datasources.py` / `catalog.py` | REST 端点 |
| `backend/scripts/seed_asset.py` | 10 域与示例业务过程 |
| `backend/tests/test_asset_datasource.py` / `test_asset_sync.py` | 用例 |
| `frontend/src/api/datasource.ts` / `catalog.ts` | 前端 API |
| `frontend/src/views/datasource/DataSourceList.vue` | 数据源页 |
| `frontend/src/views/catalog/CatalogView.vue` / `TableDetail.vue` | 目录页与表详情 |

---

### Task 1: 凭据加密

- [ ] 写测试：`encrypt_text("abc") != "abc"`，`decrypt_text(encrypt_text("abc")) == "abc"`，密文不含明文。
- [ ] 实现 `app/core/crypto.py`：`hashlib.sha256(SECRET_KEY)` → `Fernet`；`encrypt_text` / `decrypt_text`（解密失败返回空串）。
- [ ] 运行 `pytest tests/test_asset_datasource.py::test_crypto_roundtrip -v`，期望 PASS。

### Task 2: 元数据适配器

- [ ] 定义 `RemoteTable` / `RemoteColumn` dataclass 与 `MetadataAdapter` 协议（`test_connection` / `is_readonly` / `fetch_tables`）。
- [ ] 实现 `PostgresAdapter`：`create_engine(url, pool_pre_ping=True)`；表清单查 `pg_class + pg_stat_user_tables`，字段查 `information_schema.columns + col_description`，主键查 `table_constraints + key_column_usage`；schema 列表参数化拼接。
- [ ] 只读判定：`select rolsuper from pg_roles where rolname = current_user` 为 false 视为只读账号。

### Task 3: 资产模型与建表

- [ ] 新增 6 个模型文件，字段注释齐全，唯一键：数据源 `name`；表 `(datasource_id, schema_name, table_name)`；字段 `(table_id, column_name)`。
- [ ] `scripts/seed_asset.py`：插入 10 个域（mkt/prd/net/dsp/wqm/svc/ast/drn/prj/she）并标注 mkt、svc 已打样；幂等。
- [ ] 运行 `PYTHONPATH=. python scripts/seed_asset.py`，期望输出“资产基础数据初始化完成”。

### Task 4: 归类与同步

- [ ] `classify_table(name)` 规则：`^dim_`→(DIM,None,C)；`^dwd_([a-z]{3})_`→(DWD,域,A)；`^dws_([a-z]{3})_`→(DWS,域,D)；`^dws_nrw_`→(DWS,None,D)；未知→(OTHER,None,None)。
- [ ] `sync_datasource(db, ds, operator)`：拉取 → 表 upsert（更新结构字段、保留人工标注、远端消失置 MISSING）→ 字段 upsert（同理，`ds` 字段自动置分区键）→ 计数写 `ast_sync_log`。
- [ ] 测试：用伪造 adapter 传入 3 表快照，断言新增计数、二次同步幂等、人工 `business_name` 不被覆盖。

### Task 5: API

- [ ] `/datasources` CRUD（响应不含密码）、`POST /{id}/test`、`POST /{id}/sync`、`GET /{id}/sync-logs`。
- [ ] `GET /domains`、`GET /subjects`、`GET /tables`（筛选 datasource_id/layer/domain_code/keyword）、`GET /tables/{id}`、`PATCH /tables/{id}`、`GET /tables/{id}/columns`、`PATCH /columns/{id}`。
- [ ] 权限点追加 `ast:datasource` / `ast:catalog` 等 7 个，路由挂 `require_perm`。

### Task 6: 前端

- [ ] `api/datasource.ts`、`api/catalog.ts`。
- [ ] 数据源页：列表 + 新建/编辑抽屉 + 测试连接 + 同步 + 日志抽屉。
- [ ] 目录页：左侧域树、右侧表列表（筛选）；表详情页两 tab（基本信息 / 字段清单，可编辑中文名与敏感级别）。
- [ ] 路由与菜单挂载，菜单权限 `meta.anyPerm`。

### Task 7: 端到端验收

- [ ] 建数据源指向 `water_dw`（schema `cdm,cdm_mock`），点同步。
- [ ] 断言：表数 72（36×2），字段数 > 300，`dwd_mkt_meter_reading` 归 mkt/DWD/A 档，`dim_cust` 归 DIM/公共维度。
- [ ] 二次同步：新增 0、变更 0、消失 0（幂等）。
