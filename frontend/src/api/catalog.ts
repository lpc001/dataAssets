import http from './http'

export interface Domain {
  id: number
  domain_code: string
  domain_name: string
  sort: number
  description: string | null
  asset_count: number
}

export interface DomainPatch {
  domain_name?: string
  description?: string | null
  sort?: number
}

export interface DomainCreate {
  domain_code: string
  domain_name: string
  description?: string | null
  sort?: number
}

export interface ResourceTable {
  id: number
  datasource_id: number
  schema_name: string
  table_name: string
  table_comment: string | null
  table_kind: string
  is_system: boolean
  is_temp: boolean
  row_count: number | null
  column_count: number
  suggested_layer: string | null
  suggested_domain: string | null
  suggested_trace: string | null
  remote_status: string
  registered: boolean
  asset_id: number | null
  asset_status: string | null
}

export interface ResourceColumn {
  id: number
  resource_table_id: number
  column_name: string
  ordinal: number
  data_type: string | null
  is_nullable: boolean
  is_primary_key: boolean
  column_comment: string | null
  is_partition_key: boolean
  remote_status: string
}

export interface ResourceDetail extends ResourceTable {
  columns: ResourceColumn[]
}

export interface Asset {
  id: number
  asset_code: string | null
  asset_name: string
  description: string | null
  domain_code: string | null
  subject_id: number | null
  owner_domain_code: string | null
  trace_level: string | null
  status: string
  owner_name: string | null
  created_at: string | null
  resource_table_id: number
  group_type: string
  schema_name: string
  table_name: string
  data_layer: string | null
  row_count: number | null
}

export interface AssetColumn {
  id: number
  asset_id: number
  column_name: string
  ordinal: number
  business_name: string | null
  business_meaning: string | null
  sensitive_level: string
  is_key: boolean
  data_type: string | null
  column_comment: string | null
}

export interface AssetDetail extends Asset {
  columns: AssetColumn[]
}

export interface ResourcePage {
  items: ResourceTable[]
  total: number
}

export interface AssetPage {
  items: Asset[]
  total: number
}

export function listDomains(): Promise<Domain[]> {
  return http.get('/domains').then((r) => r.data)
}

export function createDomain(payload: DomainCreate): Promise<Domain> {
  return http.post('/domains', payload).then((r) => r.data)
}

export function patchDomain(id: number, payload: DomainPatch): Promise<Domain> {
  return http.patch(`/domains/${id}`, payload).then((r) => r.data)
}

export function deleteDomain(id: number) {
  return http.delete(`/domains/${id}`)
}

export function listResources(params: Record<string, unknown>): Promise<ResourcePage> {
  return http.get('/resources', { params }).then((r) => r.data)
}

export interface PreviewData {
  columns: string[]
  rows: (string | number | boolean | null)[][]
  limit: number
  schema_name: string
  table_name: string
  masked_columns: string[]
  all_columns: string[]
}

export interface PreviewQuery {
  limit?: number
  columns?: string[]
}

function previewParams(q: PreviewQuery) {
  const params: Record<string, unknown> = { limit: q.limit ?? 20 }
  if (q.columns && q.columns.length) params.columns = q.columns.join(',')
  return params
}

export function previewResource(id: number, q: PreviewQuery = {}): Promise<PreviewData> {
  return http.get(`/resources/${id}/preview`, { params: previewParams(q) }).then((r) => r.data)
}

export function previewAsset(id: number, q: PreviewQuery = {}): Promise<PreviewData> {
  return http.get(`/assets/${id}/preview`, { params: previewParams(q) }).then((r) => r.data)
}


export function patchResource(id: number, payload: { is_temp?: boolean; is_system?: boolean }) {
  return http.patch(`/resources/${id}`, payload).then((r) => r.data)
}

export function getResource(id: number): Promise<ResourceDetail> {
  return http.get(`/resources/${id}`).then((r) => r.data)
}

export interface RegisterItem {
  resource_id: number
  group_type?: string | null
  asset_name?: string | null
  domain_code?: string | null
  trace_level?: string | null
  owner_name?: string | null
}

export function registerAssets(datasource_id: number, items: RegisterItem[]): Promise<Asset[]> {
  return http.post('/assets/register', { datasource_id, items }).then((r) => r.data)
}

export function listAssets(params: Record<string, unknown>): Promise<AssetPage> {
  return http.get('/assets', { params }).then((r) => r.data)
}

export function getAsset(id: number): Promise<AssetDetail> {
  return http.get(`/assets/${id}`).then((r) => r.data)
}

export function patchAsset(id: number, payload: Record<string, unknown>) {
  return http.patch(`/assets/${id}`, payload).then((r) => r.data)
}

export function patchAssetColumn(id: number, payload: Record<string, unknown>) {
  return http.patch(`/asset-columns/${id}`, payload).then((r) => r.data)
}

export function assetSummary(): Promise<{
  datasource_count: number
  resource_count: number
  asset_count: number
  column_count: number
  domain_count: number
  missing_count: number
}> {
  return http.get('/asset-summary').then((r) => r.data)
}
