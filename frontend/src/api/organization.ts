import http from './http'

export interface Organization {
  id: number
  code: string
  name: string
  parent_id: number | null
  type: string
  sort: number
}

export interface OrganizationCreate {
  code: string
  name: string
  parent_id?: number | null
  type: string
  sort?: number
}

export function listOrganizations(): Promise<Organization[]> {
  return http.get('/organizations').then((r) => r.data)
}

export function createOrganization(data: OrganizationCreate): Promise<Organization> {
  return http.post('/organizations', data).then((r) => r.data)
}

export function updateOrganization(id: number, data: Partial<OrganizationCreate>): Promise<Organization> {
  return http.put(`/organizations/${id}`, data).then((r) => r.data)
}

export function deleteOrganization(id: number): Promise<void> {
  return http.delete(`/organizations/${id}`).then(() => undefined)
}
