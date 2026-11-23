import { defineStore } from 'pinia'
import { getMe, login as apiLogin, type MeInfo } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    me: null as MeInfo | null,
    loading: false,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => !!state.me?.is_admin,
    permissions: (state) => state.me?.permissions ?? [],
    displayName: (state) => state.me?.full_name || state.me?.username || '',
  },
  actions: {
    async login(username: string, password: string) {
      const result = await apiLogin(username, password)
      this.token = result.access_token
      localStorage.setItem('token', result.access_token)
      await this.loadMe()
    },
    async loadMe() {
      if (!this.token) return
      this.loading = true
      try {
        this.me = await getMe()
      } catch {
        this.me = null
      } finally {
        this.loading = false
      }
    },
    /** 已登录但还没拿到权限信息时（例如刷新页面）先补一次 */
    async ensureMe() {
      if (this.token && !this.me) await this.loadMe()
    },
    hasPerm(code: string) {
      return this.isAdmin || this.permissions.includes(code)
    },
    hasAnyPerm(codes: string[]) {
      return this.isAdmin || codes.some((c) => this.permissions.includes(c))
    },
    logout() {
      this.token = ''
      this.me = null
      localStorage.removeItem('token')
    },
  },
})
