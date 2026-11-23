# 平台基础框架（Platform Base）

新平台起步用的统一底座：**只含系统管理模块**（组织、用户、角色与功能权限、数据权限、品牌设置），不含任何具体业务。
后续每个业务平台从这里复制一份，保证菜单结构、页面风格、权限模型、登录与品牌定制完全一致。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | FastAPI + SQLAlchemy 2.x + Pydantic v2 + PostgreSQL（默认配置可用 SQLite 跑通） |
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Pinia + Vue Router |
| 鉴权 | OAuth2 Password（JWT），功能权限按模块划分，数据权限按组织范围划分 |

## 目录结构

```text
backend/
  app/
    api/v1/        auth / users / roles / organizations / brand
    core/          config / database / security / permissions（权限点清单）
    crud/          organization / role / role_data_scope / user / user_role
    models/        organization / role / role_data_scope / role_permission / user / brand
    schemas/
    services/      permissions（功能权限校验）/ data_scope（组织范围解析）/ brand
    main.py
  scripts/         seed.py（初始管理员）/ seed_brand.py（品牌）
  tests/           系统管理相关用例
frontend/
  src/
    api/           http / auth / user / role / organization / brand
    layouts/       MainLayout.vue（侧栏 + 顶栏）
    stores/        auth / brand
    views/         Login / organization / user / role / system/BrandSettings
    router/        路由与权限守卫
    styles/theme.css  设计变量（颜色、圆角、阴影）
docs/
  设计规范.md      前端视觉与交互规范
```

## 快速开始

### 1. 后端

```bash
cd backend
pip install -r requirements.txt
cp env.example .env           # 按需修改数据库连接（.env 已被 .gitignore 忽略）
python scripts/seed.py        # 建表 + 初始管理员 admin / admin123
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- 健康检查：`GET http://localhost:8000/health`
- 接口文档：`http://localhost:8000/docs`
- 默认账号：`admin / admin123`（首次登录后请改密码）

### 2. 前端

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173，/api 已代理到 8000
```

也可以在项目根目录双击 `start-backend.bat` / `start-frontend.bat`（Windows）。

## 权限模型

**功能权限**（`app/core/permissions.py`）：一个模块一个权限点。

| 权限编码 | 名称 | 管什么 |
| --- | --- | --- |
| `system:org` | 组织管理 | 组织增删改 |
| `system:user` | 用户管理 | 用户增删改、分配角色 |
| `system:role` | 角色管理 | 角色增删改、功能授权、数据权限 |
| `system:brand` | 品牌设置 | 系统名称与 Logo |

- `ADMIN` 角色绕过所有校验；
- 角色没有任何权限记录时默认**无功能权限**，只能改自己的资料；
- 后端用 `Depends(require_perm("x"))`，前端用路由 `meta.anyPerm` + 菜单过滤，两端同一份编码。

**数据权限**（`sys_role_data_scope`）：`ALL` / `ORG_AND_CHILD` / `ORG_ONLY` / `CUSTOM`。
需要按组织收敛业务数据时，调用 `app/services/data_scope.allowed_org_codes(db, user)` 取允许的组织编码（`None` 表示不限）。

## 品牌定制

- 页面：系统管理 → 品牌设置（预览、名称、副标题、上传 Logo、恢复默认）；
- 存储：`sys_brand` 单行表，Logo 存 base64 data URL，随库备份；
- 命令行：`python scripts/seed_brand.py --name "某某平台" --subtitle "副标题"`；
- 生效位置：侧栏左上角、顶栏面包屑、登录页。

## 接入新业务模块的做法

1. 后端：新增 `models/ crud/ schemas/ api/v1/` 对应模块，在 `api/v1/__init__.py` 挂路由，在 `core/permissions.py` 加权限点；
2. 前端：新增 `api/`、`views/`，在 `router/index.ts` 加路由（写 `meta.anyPerm`），在 `MainLayout.vue` 的 `allMenus` 加菜单项；
3. 角色管理里给对应角色勾上新权限点即可。
