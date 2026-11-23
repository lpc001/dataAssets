import { defineStore } from 'pinia'
import { getBrand } from '@/api/brand'

/** 品牌信息（Logo + 名称），全站共用，登录页也会用到 */
export const useBrandStore = defineStore('brand', {
  state: () => ({
    name: '',
    subtitle: '',
    logo: '',
    loaded: false,
  }),
  getters: {
    /** 名称按「·」拆成两段：前半常规字重，后半加粗（沿用原标题样式） */
    parts: (state) => {
      const name = state.name || '水投·指标平台'
      const idx = name.indexOf('·')
      if (idx < 0) return { head: name, tail: '' }
      return { head: name.slice(0, idx + 1), tail: name.slice(idx + 1) }
    },
  },
  actions: {
    async load(force = false) {
      if (this.loaded && !force) return
      try {
        const info = await getBrand()
        this.name = info.name
        this.subtitle = info.subtitle
        this.logo = info.logo
      } catch {
        // 后端未就绪时保持默认，不影响登录页渲染
      } finally {
        this.loaded = true
      }
    },
  },
})
