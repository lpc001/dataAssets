"""功能权限定义。

权限点按「模块」划分，一个模块一个权限点，够用且配置简单。
角色没有任何权限记录时按 DEFAULT_ROLE_PERMISSIONS 处理（默认无任何功能权限，只能改自己的资料）；
ADMIN 角色视为超级管理员，绕过所有功能权限判断。

新平台接入时：在这里追加业务模块的权限点即可，前后端都靠这份清单。
"""

ADMIN_ROLE_CODE = "ADMIN"

# (权限编码, 名称, 分组)
PERMISSIONS: list[tuple[str, str, str]] = [
    ("system:org", "组织管理", "系统管理"),
    ("system:user", "用户管理", "系统管理"),
    ("system:role", "角色管理", "系统管理"),
    ("system:brand", "品牌设置", "系统管理"),
    ("ast:datasource", "数据源管理", "数据资产"),
    ("ast:catalog", "资产目录", "数据资产"),
    ("ast:indicator", "指标中心", "数据资产"),
    ("ast:lineage", "血缘", "数据资产"),
    ("ast:preview", "数据预览", "数据资产"),
    ("ast:standard", "规范中心", "数据资产"),
]

PERMISSION_NAMES: dict[str, str] = {code: name for code, name, _ in PERMISSIONS}

# 角色未配置任何权限时默认拥有（基础框架默认不给任何功能权限）
DEFAULT_ROLE_PERMISSIONS: frozenset[str] = frozenset()


def all_codes() -> list[str]:
    return [code for code, _, _ in PERMISSIONS]


def perm_name(code: str) -> str:
    return PERMISSION_NAMES.get(code, code)
