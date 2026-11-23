# 指标中心设计方案（v1.1 · 资产驱动）

- 版本：v1.1（替代 v1.0 的"台账导入驱动"）
- 日期：2026-11-23
- 变更要点：v1.0 从 `dim_indicator` / `dim_caliber_dict` 出发维护指标，属结果向；v1.1 改为**从数据资产维护指标，台账是发布的产物**。

---

## 1. 定位

平台是**指标的定义与治理源头**；`dim_indicator` / `dim_caliber_dict` 是发布出去的**标准化台账**，供下游大屏、报表、模型使用。

```text
资产字段（已登记、有注释、有敏感级别）
      │  ① 基于字段创建指标
      ▼
  指标草稿（名称/定义/公式/单位/周期）
      │  ② 关联或新建口径
      ▼
  校验（引用完整性 / 公式可解析 / 口径一致）
      │  ③ 人工确认发布
      ▼
  平台指标目录 ──④ 发布台账──▶ dim_indicator / dim_caliber_dict
```

## 2. 已确认决策

| 决策 | 结论 |
|---|---|
| 审批流 | 不做，只做校验门禁 + 人工确认 |
| 存量台账 | 一次性迁移为草稿，不是日常流程入口 |
| 指标与口径 | 一对一（指标表放 `caliber_id`，不建中间表） |
| 流程起点 | **数据资产字段**，不是台账表 |

## 3. 主流程（日常）

1. **入口**：资产目录 → 资产详情 → 字段清单 → 选中字段 → 「基于此字段创建指标」；
2. **起草**：来源字段自动带出且不可手填；填写名称、编码（自动生成可改）、定义、单位、周期、公式；
3. **口径**：可直接新建口径（与本指标一对一）或选择已有口径；
4. **校验**：实时跑规则，阻断项未清零不能发布；
5. **发布**：平台内进入指标目录，同时可选择"发布台账"回写目标库；
6. **变更**：已发布指标修改 → 自动退回草稿 → 重新校验 → 再次发布，全过程留版本。

非资产字段的指标不允许存在——**指标必须从资产字段长出**，这是和 v1.0 最本质的区别。

## 4. 数据模型

### 4.1 `ast_indicator`

indicator_code / indicator_name / theme / domain_code / indicator_level / indicator_type / indicator_def / formula / unit / cycle / **source_asset_column_id** / **carry_asset_column_id** / carry_type / **caliber_id** / status（DRAFT/PUBLISHED/RETIRED）/ source_type（HUMAN/AI/IMPORT）/ owner_name / publish_status（NONE/PUBLISHED/OUTDATED）/ published_at / created_at / updated_at。

### 4.2 `ast_caliber`

caliber_code / caliber_name / caliber_def / formula / source_fields / value_type（标准/可配置）/ apply_layer / caliber_kind（INDICATOR/ENUM/SLA） / status / source_type / owner_name。

> 存量 `dim_caliber_dict` 混了枚举与时限，导入时按编码前缀归类：`ENUM_*` → 枚举、`CAL_SVC_*` 时限类 → SLA、其余 → 指标口径。

### 4.3 `ast_governance_rule`

rule_code / rule_name / target / severity（BLOCK/WARN）/ params(JSON) / enabled / description。

### 4.4 `ast_indicator_version`

object_type / object_id / version_no / changed_by / changed_at / changes(JSON)。

### 4.5 `ast_publish_log`

publish_type（PLATFORM/TARGET）/ object_type / object_ids / target_datasource_id / mode（SQL/EXCEL/WRITE）/ operator / created_at / result。

## 5. 校验规则

| 编码 | 规则 | 级别 |
|---|---|---|
| R01 | 必填完整（编码/名称/定义/公式/单位/周期） | 阻断 |
| R02 | 编码唯一且符合主题码规范 | 阻断 |
| R03 | 来源字段必须来自已登记资产字段（外键天然保证） | 阻断 |
| R04 | 承载字段存在且为数值型 | 阻断 |
| R05 | 公式可解析（字段名/运算符/函数），非自然语言 | 阻断 |
| R06 | 必须关联口径 | 警告 |
| R07 | 同域内名称不重复 | 警告 |
| R08 | 暂缓/跨域指标不得挂承载字段 | 警告 |
| R09 | 单位/周期与类型匹配（比率 %、金额 元） | 警告 |
| R10 | 已发布指标必须有责任人 | 警告 |

## 6. 存量迁移（一次性，不是日常入口）

1. 读取目标库 `dim_indicator` / `dim_caliber_dict`；
2. 按前缀把口径拆为 INDICATOR / ENUM / SLA 三类；
3. 解析 `source_table_field → 资产字段`，生成草稿并挂载；
4. 解析失败的进"待挂载"清单，人工补挂或标记废止；
5. 全部草稿，人工修订后发布。

实测存量情况：53 项指标中 **36 项可直接挂到资产字段**，17 项解析失败（典型写法：只写表名 `dim_cust`、表名+条件 `dwd_mkt_billing(bill_status)`）；3 项未填口径；38 条口径中 24 条未被引用（多为枚举/时限）。

## 7. 发布台账（回写目标库）

三种方式，建议分期：

| 方式 | 说明 | 建议 |
|---|---|---|
| **SQL 导出** | 生成 upsert 脚本，人工执行 | 一期先做，零风险 |
| Excel 导出 | 生成标准模板文件供导入 | 一期可做 |
| **直接回写** | 平台用写权限账号 upsert 到目标库 | 二期，需单独配置写账号 |

回写约定：以 `indicator_code` / `caliber_code` 为业务主键 upsert；废止不物理删除，写 `status=RETIRED`；每次发布写 `ast_publish_log`。

## 8. 界面

| 页面 | 内容 |
|---|---|
| 资产详情 · 字段清单 | 每行新增「创建指标」入口（预填来源字段） |
| 指标中心 | 列表（编码/名称/状态/校验/来源资产字段/口径/发布状态）+ 筛选 + 新建 |
| 指标详情 | 表单、校验面板、版本历史、发布记录 |
| 口径管理 | 列表（按三类分组）、关联指标、编辑 |
| 规则管理 | 规则开关与级别 |
| 台账发布 | 选择指标 → 生成 SQL / 导出 Excel / 回写 |

## 9. 分期

| 阶段 | 内容 |
|---|---|
| I1 | 指标/口径/规则/版本表；从资产字段创建指标；校验；指标列表与详情 |
| I2 | 口径管理、发布门禁、版本历史 |
| I3 | 台账发布（SQL/Excel，再回写）、存量迁移工具、健康巡检 |

## 10. 风险

- 回写需要写权限账号，与只读采集账号分离，需单独配置；
- 目标库台账字段与平台字段需要映射表，字段缺失时报错而不是静默跳过；
- 存量 17 项解析失败需人工补齐，属一次性成本。

---

本文件由水务加出品的 WaterPlusAI 辅助编制，资料来源以文中标注为准。本文件供内部研讨参考，正式决策请以权威文件和内部数据为准。
