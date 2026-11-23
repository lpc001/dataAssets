import http from './http'

export interface Role {
  id: number
  name: string
  code: string
  description: string
}

export interface RoleCreate {
  name: string
  code: string
  description?: string
}

export interface RoleDataScope {
  id: number
  role_id: number
  scope_type: string
  custom_org_ids: string
}

export interface RoleUser {
  id: number
  username: string
  name: string
  org_id: number | null
  status: string
}

export function listRoles(): Promise<Role[]> {
  return http.get('/roles').then((r) => r.data)
}

export function createRole(data: RoleCreate): Promise<Role> {
  return http.post('/roles', data).then((r) => r.data)
}

export function updateRole(id: number, data: Partial<RoleCreate>): Promise<Role> {
  return http.put(`/roles/${id}`, data).then((r) => r.data)
}

export function deleteRole(id: number): Promise<void> {
  return http.delete(`/roles/${id}`).then(() => undefined)
}

export function getRoleDataScope(id: number): Promise<RoleDataScope> {
  return http.get(`/roles/${id}/data-scope`).then((r) => r.data)
}

export function setRoleDataScope(
  id: number,
  data: { scope_type: string; custom_org_ids: number[] },
): Promise<RoleDataScope> {
  return http.put(`/roles/${id}/data-scope`, data).then((r) => r.data)
}

export function listRoleUsers(id: number): Promise<RoleUser[]> {
  return http.get(`/roles/${id}/users`).then((r) => r.data)
}

export function setRoleUsers(id: number, userIds: number[]): Promise<RoleUser[]> {
  return http.put(`/roles/${id}/users`, { user_ids: userIds }).then((r) => r.data)
}

export interface RolePermissionInfo {
  role_id: number
  permissions: string[]
  is_default: boolean
}

export interface PermissionItem {
  code: string
  name: string
  group: string
}

export function getRolePermissions(id: number): Promise<RolePermissionInfo> {
  return http.get(`/roles/${id}/permissions`).then((r) => r.data)
}

export function setRolePermissions(id: number, permissions: string[]): Promise<RolePermissionInfo> {
  return http.put(`/roles/${id}/permissions`, { permissions }).then((r) => r.data)
}

export function getPermissionCatalog(): Promise<PermissionItem[]> {
  return http.get('/roles/permissions/catalog').then((r) => r.data)
}
