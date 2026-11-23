import http from './http'
import type { Role } from './role'

export interface User {
  id: number
  username: string
  name: string
  org_id: number | null
  status: string
  created_at: string
}

export interface UserCreate {
  username: string
  name?: string
  org_id?: number | null
  status?: string
  password: string
}

export function listUsers(): Promise<User[]> {
  return http.get('/users').then((r) => r.data)
}

export function createUser(data: UserCreate): Promise<User> {
  return http.post('/users', data).then((r) => r.data)
}

export function updateUser(id: number, data: Partial<UserCreate>): Promise<User> {
  return http.put(`/users/${id}`, data).then((r) => r.data)
}

export function deleteUser(id: number): Promise<void> {
  return http.delete(`/users/${id}`).then(() => undefined)
}

export function getUserRoles(id: number): Promise<Role[]> {
  return http.get(`/users/${id}/roles`).then((r) => r.data)
}

export function setUserRoles(id: number, roleIds: number[]): Promise<Role[]> {
  return http.put(`/users/${id}/roles`, { role_ids: roleIds }).then((r) => r.data)
}
