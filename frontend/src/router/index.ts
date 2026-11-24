import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    /** 需要其中之一的功能权限，全部不满足则看不到该页 */
    anyPerm?: string[]
    /** 出现在菜单里的名称 */
    title?: string
    /** 菜单分组 */
    group?: string
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
    },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      redirect: '/users',
      children: [
        {
          path: 'organizations',
          name: 'organizations',
          component: () => import('@/views/organization/OrganizationList.vue'),
          meta: {
            title: '组织管理',
            group: '系统管理',
            anyPerm: ['system:org', 'system:user', 'system:role'],
          },
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/user/UserList.vue'),
          meta: { title: '用户管理', group: '系统管理', anyPerm: ['system:user'] },
        },
        {
          path: 'roles',
          name: 'roles',
          component: () => import('@/views/role/RoleList.vue'),
          meta: { title: '角色管理', group: '系统管理', anyPerm: ['system:role'] },
        },
        {
          path: 'brand',
          name: 'brand',
          component: () => import('@/views/system/BrandSettings.vue'),
          meta: { title: '品牌设置', group: '系统管理', anyPerm: ['system:brand'] },
        },
        {
          path: 'map',
          name: 'data-map',
          component: () => import('@/views/map/DataMap.vue'),
          meta: { title: '数据全景', group: '数据资产', anyPerm: ['ast:catalog'] },
        },
        {
          path: 'datasource',
          name: 'datasource',
          component: () => import('@/views/datasource/DataSourceList.vue'),
          meta: { title: '数据源管理', group: '数据资产', anyPerm: ['ast:datasource'] },
        },
        {
          path: 'resources',
          name: 'resources',
          component: () => import('@/views/catalog/ResourcePool.vue'),
          meta: { title: '资源池', group: '数据资产', anyPerm: ['ast:catalog'] },
        },
        {
          path: 'catalog',
          name: 'catalog',
          component: () => import('@/views/catalog/CatalogView.vue'),
          meta: { title: '资产目录', group: '数据资产', anyPerm: ['ast:catalog'] },
        },
        {
          path: 'domains',
          name: 'domains',
          component: () => import('@/views/catalog/DomainSettings.vue'),
          meta: { title: '数据域', group: '数据资产', anyPerm: ['ast:catalog'] },
        },
        {
          path: 'indicators',
          name: 'indicators',
          component: () => import('@/views/indicator/IndicatorList.vue'),
          meta: { title: '指标中心', group: '数据资产', anyPerm: ['ast:indicator'] },
        },
        {
          path: 'indicators/new',
          name: 'indicator-new',
          component: () => import('@/views/indicator/IndicatorForm.vue'),
          meta: { title: '新建指标', group: '数据资产', anyPerm: ['ast:indicator'] },
        },
        {
          path: 'indicators/:id',
          name: 'indicator-detail',
          component: () => import('@/views/indicator/IndicatorDetail.vue'),
          meta: { title: '指标详情', group: '数据资产', anyPerm: ['ast:indicator'] },
        },
        {
          path: 'catalog/:id',
          name: 'asset-detail',
          component: () => import('@/views/catalog/AssetDetail.vue'),
          meta: { title: '资产详情', group: '数据资产', anyPerm: ['ast:catalog'] },
        },
      ],
    },
  ],
})

/** 按顺序返回该用户第一个有权限访问的菜单路由 */
export function firstAllowedPath(): string {
  const auth = useAuthStore()
  for (const parent of router.options.routes) {
    for (const child of parent.children ?? []) {
      const anyPerm = child.meta?.anyPerm
      if (!anyPerm || auth.hasAnyPerm(anyPerm as string[])) {
        return '/' + child.path
      }
    }
  }
  return '/login'
}

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.path === '/login') {
    return true
  }
  if (!auth.isLoggedIn) {
    return { path: '/login' }
  }

  await auth.ensureMe()

  if (to.path === '/') {
    return firstAllowedPath()
  }

  const anyPerm = to.meta.anyPerm as string[] | undefined
  if (anyPerm && !auth.hasAnyPerm(anyPerm)) {
    const fallback = firstAllowedPath()
    return fallback === to.path ? true : { path: fallback }
  }
  return true
})

export default router
