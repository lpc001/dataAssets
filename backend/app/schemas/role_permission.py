from pydantic import BaseModel


class RolePermissionRead(BaseModel):
    role_id: int
    permissions: list[str] = []
    # 该角色是否「未配置过权限」，前端据此提示按默认权限处理
    is_default: bool = False


class RolePermissionUpdate(BaseModel):
    permissions: list[str] = []
