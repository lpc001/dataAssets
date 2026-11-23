import http from './http'

export interface BrandInfo {
  id: number
  name: string
  subtitle: string
  logo: string
}

export function getBrand(): Promise<BrandInfo> {
  return http.get('/brand').then((r) => r.data)
}

export function updateBrand(payload: Partial<BrandInfo>): Promise<BrandInfo> {
  return http.put('/brand', payload).then((r) => r.data)
}

export function resetBrand(): Promise<BrandInfo> {
  return http.post('/brand/reset').then((r) => r.data)
}
