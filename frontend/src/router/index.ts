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
