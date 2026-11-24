<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">
        <img v-if="brand.logo" :src="brand.logo" class="logo-img" alt="logo" />
        <span v-else class="drop"></span>
        <span>{{ brand.parts.head }}<b>{{ brand.parts.tail }}</b></span>
      </div>
      <template v-for="g in visibleGroups" :key="g.name">
        <div class="nav-group">{{ g.name }}</div>
        <router-link
          v-for="item in g.items"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path.startsWith(item.path) }"
          >{{ item.title }}</router-link
        >
      </template>
    </aside>
    <div class="main">
      <header class="topbar">
        <span class="crumb">{{ brand.name || '水务指标平台' }}</span>
        <div class="user-area">
          <span class="avatar">{{ avatarText }}</span>
          <span class="user-name">{{ auth.me?.full_name || auth.me?.username }}</span>
          <el-button text @click="openProfile">我的资料</el-button>
          <el-button text @click="onLogout">退出登录</el-button>
        </div>
      </header>
      <main class="content">
        <router-view />
      </main>
    </div>

    <!-- 我的资料 -->
    <el-dialog v-model="profileVisible" title="我的资料" width="440px">
      <el-form :model="profileForm" label-width="90px" @submit.prevent>
        <el-form-item label="登录账号">
          <span class="mono">{{ auth.me?.username }}</span>
        </el-form-item>
        <el-form-item label="所属组织">
          <span>{{ auth.me?.org_name || '—' }}</span>
        </el-form-item>
        <el-form-item label="角色">
          <span>{{ auth.me?.roles?.join('、') || '—' }}</span>
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="profileForm.name" maxlength="30" />
        </el-form-item>
        <el-form-item label="密码">
          <el-button link type="primary" @click="openChangePassword">修改密码</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="profileVisible = false">取消</el-button>
        <el-button type="primary" :loading="profileSaving" @click="onSaveProfile">保存</el-button>
      </template>
    </el-dialog>

    <!-- 修改密码 -->
    <el-dialog v-model="pwdVisible" title="修改密码" width="440px">
      <el-form label-width="96px" @submit.prevent>
        <el-form-item label="旧密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password placeholder="当前密码" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="pwdForm.confirm_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="pwdSaving" @click="onSavePassword">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { updateMe } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { useBrandStore } from '@/stores/brand'

const router = useRouter()
const auth = useAuthStore()
const brand = useBrandStore()

interface MenuItem {
  path: string
  title: string
  group: string
  anyPerm?: string[]
}

const allMenus: MenuItem[] = [
  { path: '/map', title: '数据全景', group: '数据资产', anyPerm: ['ast:catalog'] },
  { path: '/datasource', title: '数据源管理', group: '数据资产', anyPerm: ['ast:datasource'] },
  { path: '/resources', title: '资源池', group: '数据资产', anyPerm: ['ast:catalog'] },
  { path: '/catalog', title: '资产目录', group: '数据资产', anyPerm: ['ast:catalog'] },
  { path: '/domains', title: '数据域', group: '数据资产', anyPerm: ['ast:catalog'] },
  { path: '/indicators', title: '指标中心', group: '数据资产', anyPerm: ['ast:indicator'] },
  {
    path: '/organizations',
    title: '组织管理',
    group: '系统管理',
    anyPerm: ['system:org', 'system:user', 'system:role'],
  },
  { path: '/users', title: '用户管理', group: '系统管理', anyPerm: ['system:user'] },
  { path: '/roles', title: '角色管理', group: '系统管理', anyPerm: ['system:role'] },
  { path: '/brand', title: '品牌设置', group: '系统管理', anyPerm: ['system:brand'] },
]

const visibleGroups = computed(() => {
  const groups: { name: string; items: MenuItem[] }[] = []
  for (const item of allMenus) {
    if (item.anyPerm && !auth.hasAnyPerm(item.anyPerm)) continue
    let g = groups.find((x) => x.name === item.group)
    if (!g) {
      g = { name: item.group, items: [] }
      groups.push(g)
    }
    g.items.push(item)
  }
  return groups
})

const avatarText = computed(() => (auth.me?.full_name || auth.me?.username || '·').slice(0, 1))

onMounted(() => {
  auth.ensureMe()
  brand.load()
})

const profileVisible = ref(false)
const profileSaving = ref(false)
const profileForm = reactive({ name: '' })

function openProfile() {
  profileForm.name = auth.me?.full_name || ''
  profileVisible.value = true
}

async function onSaveProfile() {
  const payload: { name?: string } = {}
  if (profileForm.name && profileForm.name !== (auth.me?.full_name || '')) {
    payload.name = profileForm.name
  }
  if (!payload.name) {
    ElMessage.info('没有需要保存的修改')
    return
  }
  profileSaving.value = true
  try {
    await updateMe(payload)
    ElMessage.success('已保存')
    profileVisible.value = false
    await auth.loadMe()
  } finally {
    profileSaving.value = false
  }
}

const pwdVisible = ref(false)
const pwdSaving = ref(false)
const pwdForm = reactive({ old_password: '', new_password: '', confirm_password: '' })

function openChangePassword() {
  pwdForm.old_password = ''
  pwdForm.new_password = ''
  pwdForm.confirm_password = ''
  pwdVisible.value = true
}

async function onSavePassword() {
  if (!pwdForm.old_password) {
    ElMessage.warning('请输入旧密码')
    return
  }
  if (pwdForm.new_password.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  if (pwdForm.new_password !== pwdForm.confirm_password) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  pwdSaving.value = true
  try {
    // 旧密码由后端在保存时校验，不一致会返回 400「原密码不正确」
    await updateMe({ old_password: pwdForm.old_password, new_password: pwdForm.new_password })
    ElMessage.success('密码已修改，下次登录请使用新密码')
    pwdVisible.value = false
  } finally {
    pwdSaving.value = false
  }
}

function onLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout {
  display: flex;
  height: 100%;
}
.sidebar {
  width: 220px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  padding: 20px 0;
  display: flex;
  flex-direction: column;
}
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text);
  padding: 0 20px 20px;
}
.logo b {
  color: var(--color-primary);
}
.drop {
  width: 14px;
  height: 14px;
  border-radius: 50% 50% 50% 0;
  background: var(--gradient-primary);
  transform: rotate(-45deg);
}
.nav-group {
  margin-top: 20px;
  padding: 0 20px 8px;
  font-size: 11px;
  color: #9db4c8;
  letter-spacing: 1px;
}
.nav-item {
  display: block;
  padding: 11px 20px;
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 14px;
  border-left: 3px solid transparent;
  transition: 0.15s;
}
.nav-item:hover {
  color: var(--color-primary);
  background: var(--color-tint);
}
.nav-item.active {
  color: var(--color-primary);
  background: var(--color-tint);
  border-left-color: var(--color-primary);
  font-weight: 600;
}
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.topbar {
  height: 56px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.crumb {
  font-size: 13px;
  color: var(--color-text-secondary);
}
.user-area {
  display: flex;
  align-items: center;
  gap: 10px;
}
.user-name {
  font-size: 13px;
  color: var(--color-text);
}
.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--gradient-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
}
.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
/* 品牌 Logo */
.logo-img {
  width: 30px;
  height: 30px;
  object-fit: contain;
  border-radius: 8px;
  flex: none;
}
</style>
