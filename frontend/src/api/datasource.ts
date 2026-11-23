import http from './http'

export interface DataSource {
  id: number
  name: string
  db_type: string
  host: string
  port: number
  database_name: string
  schema_filter: string
  username: string
  readonly_verified: boolean
  status: string
  last_sync_at: string | null
  remark: string | null
}

export interface DataSourcePayload {
  name: string
  host: string
  port: number
  database_name: string
  schema_filter: string
  username: string
  password?: string
  remark?: string
}

export interface MetaVersion {
  id: number
  datasource_id: number
  version_no: number
  started_at: string
  finished_at: string | null
  status: string
  table_added: number
  table_changed: number
  table_dropped: number
  column_added: number
  column_changed: number
  column_dropped: number
  operator: string | null
  message: string | null
}

export interface MetaChange {
  id: number
  version_id: number
  object_type: string
  schema_name: string
  table_name: string
  column_name: string | null
  change_type: string
  field_name: string | null
  old_value: string | null
  new_value: string | null
}

export function listDatasources(): Promise<DataSource[]> {
  return http.get('/datasources').then((r) => r.data)
}

export function createDatasource(payload: DataSourcePayload): Promise<DataSource> {
  return http.post('/datasources', payload).then((r) => r.data)
}

export function updateDatasource(id: number, payload: Partial<DataSourcePayload> & { status?: string }) {
  return http.put(`/datasources/${id}`, payload).then((r) => r.data)
}

export function deleteDatasource(id: number) {
  return http.delete(`/datasources/${id}`)
}

export function testDatasource(id: number): Promise<{ ok: boolean; readonly: boolean; message: string }> {
  return http.post(`/datasources/${id}/test`).then((r) => r.data)
}

export function syncDatasource(id: number): Promise<MetaVersion> {
  return http.post(`/datasources/${id}/sync`, null, { timeout: 180000 }).then((r) => r.data)
}

export function listVersions(id: number): Promise<MetaVersion[]> {
  return http.get(`/datasources/${id}/versions`).then((r) => r.data)
}

export function listVersionChanges(versionId: number): Promise<MetaChange[]> {
  return http.get(`/datasources/versions/${versionId}/changes`).then((r) => r.data)
}
