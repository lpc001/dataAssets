import http from './http'

export interface PathInfo {
  asset_id: number
  asset_name: string
  schema_name: string
  table_name: string
  column_name: string
  data_type: string | null
  domain_code: string | null
}

export interface ValidationInfo {
  block: number
  warn: number
}

export interface Indicator {
  id: number
  indicator_code: string
  indicator_name: string
  domain_code: string | null
  status: string
  unit: string | null
  cycle: string | null
  owner_name: string | null
  source_path: PathInfo | null
  carry_path: PathInfo | null
  validation: ValidationInfo
}

export interface IndicatorDetail extends Indicator {
  theme: string | null
  indicator_level: string | null
  indicator_type: string | null
  indicator_def: string | null
  formula: string | null
  caliber_id: number | null
  carry_type: string | null
  source_type: string
  created_at: string | null
  updated_at: string | null
  issues: { rule_code: string; rule_name: string; severity: string; message: string }[]
  versions: { version_no: number; changed_by: string | null; changed_at: string | null; comment: string | null }[]
}

export interface Caliber {
  id: number
  caliber_code: string
  caliber_name: string
  caliber_def: string | null
  formula: string | null
  source_fields: string | null
  value_type: string
  apply_layer: string | null
  caliber_kind: string
  status: string
  owner_name: string | null
}

export function listIndicators(params: Record<string, unknown>) {
  return http.get('/indicators', { params }).then((r) => r.data)
}

export function getIndicator(id: number): Promise<IndicatorDetail> {
  return http.get(`/indicators/${id}`).then((r) => r.data)
}

export function createIndicator(payload: Record<string, unknown>): Promise<IndicatorDetail> {
  return http.post('/indicators', payload).then((r) => r.data)
}

export function updateIndicator(id: number, payload: Record<string, unknown>): Promise<IndicatorDetail> {
  return http.patch(`/indicators/${id}`, payload).then((r) => r.data)
}

export function publishIndicator(id: number): Promise<IndicatorDetail> {
  return http.post(`/indicators/${id}/publish`).then((r) => r.data)
}

export function retireIndicator(id: number): Promise<IndicatorDetail> {
  return http.post(`/indicators/${id}/retire`).then((r) => r.data)
}

export function listCalibers(kind?: string): Promise<Caliber[]> {
  return http.get('/calibers', { params: kind ? { kind } : {} }).then((r) => r.data)
}

export function createCaliber(payload: Record<string, unknown>): Promise<Caliber> {
  return http.post('/calibers', payload).then((r) => r.data)
}

export function listRules() {
  return http.get('/governance-rules').then((r) => r.data)
}
