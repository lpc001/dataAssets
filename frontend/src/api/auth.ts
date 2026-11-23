import http from './http'

export interface LoginResult {
  access_token: string
  token_type: string
}

export interface MeInfo {
  id: number
  username: string
  full_name: string | null
  is_admin: boolean
  org_id: number | null
  org_name: string | null
  roles: string[]
  permissions: string[]
}

export interface SelfUpdatePayload {
  name?: string
  old_password?: string
  new_password?: string
}

export function login(username: string, password: string): Promise<LoginResult> {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)
  return http
    .post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    .then((r) => r.data)
}

export function getMe(): Promise<MeInfo> {
  return http.get('/auth/me').then((r) => r.data)
}

export function updateMe(payload: SelfUpdatePayload): Promise<{ id: number; username: string; name: string }> {
  return http.put('/users/me', payload).then((r) => r.data)
}
