<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">用户管理</div>
        <div class="page-sub">左侧选择组织，维护其下用户</div>
      </div>
      <el-button type="primary" @click="openCreate">新增用户</el-button>
    </div>

    <div class="user-layout">
      <!-- 左侧组织树 -->
      <div class="org-panel">
        <div class="panel-title">组织</div>
        <div class="all-entry" :class="{ active: currentOrgId === null }" @click="selectAll">
          全部用户
        </div>
        <el-tree
          class="org-tree"
          :data="orgTree"
          :props="{ label: 'name', children: 'children' }"
          node-key="id"
          highlight-current
          :current-node-key="currentOrgId"
          :expand-on-click-node="false"
          @node-click="onNodeClick"
        />
      </div>

      <!-- 右侧用户列表 -->
      <div class="user-panel">
        <div class="panel-title">
          用户列表
          <span class="panel-sub" v-if="currentOrgName">当前组织：{{ currentOrgName }}</span>
        </div>
        <el-table :data="filteredUsers" border stripe v-loading="loading">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="username" label="用户名" width="150" />
          <el-table-column prop="name" label="姓名" width="130" />
          <el-table-column label="所属组织" width="160">
            <template #default="{ row }">
              {{ row.org_id ? orgName(row.org_id) : '—' }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status === 'ACTIVE' ? 'success' : 'info'">
                {{ row.status === 'ACTIVE' ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="250" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="primary" @click="openRoles(row)">分配角色</el-button>
              <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑用户' : '新增用户'" width="480px">
      <el-form :model="form" label-width="90px" @submit.prevent>
        <el-form-item label="用户名">
          <el-input v-model="form.username" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="新增时必填" />
        </el-form-item>
        <el-form-item label="所属组织">
          <el-tree-select
            v-model="form.org_id"
            :data="orgTree"
            :props="{ label: 'name', children: 'children' }"
            node-key="id"
            check-strictly
            clearable
            placeholder="选择所属组织"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="启用" value="ACTIVE" />
            <el-option label="停用" value="DISABLED" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 分配角色抽屉 -->
    <el-drawer v-model="roleVisible" :title="`分配角色：${roleUser?.name || roleUser?.username || ''}`" size="420px">
      <div class="auth-section">
        <div class="auth-title">选择该用户拥有的角色</div>
        <el-select
          v-model="roleIds"
          multiple
          filterable
          placeholder="选择角色"
          style="width: 100%"
        >
          <el-option v-for="r in allRoles" :key="r.id" :label="r.name" :value="r.id" />
        </el-select>
      </div>
      <div class="auth-footer">
        <el-button type="primary" :loading="roleSaving" @click="onSaveRoles">保存</el-button>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listUsers,
  createUser,
  updateUser,
  deleteUser,
  getUserRoles,
  setUserRoles,
  type User,
} from '@/api/user'
import { listOrganizations, type Organization } from '@/api/organization'
import { listRoles, type Role } from '@/api/role'

interface OrgTreeNode {
  id: number
  name: string
  children?: OrgTreeNode[]
}

const list = ref<User[]>([])
const organizations = ref<Organization[]>([])
const allRoles = ref<Role[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
// null 表示"全部用户"视图，具体数字表示选中某个组织
const currentOrgId = ref<number | null>(null)
const form = ref<{ id?: number; username: string; name: string; password: string; org_id: number | null; status: string }>({
  username: '',
  name: '',
  password: '',
  org_id: null,
  status: 'ACTIVE',
})

// 分配角色
const roleVisible = ref(false)
const roleUser = ref<User | null>(null)
const roleIds = ref<number[]>([])
const roleSaving = ref(false)

// 组织树：由扁平列表按 parent_id 组装
const orgTree = computed<OrgTreeNode[]>(() => {
  const nodes = new Map<number, OrgTreeNode>()
  organizations.value.forEach((o) => nodes.set(o.id, { id: o.id, name: o.name }))
  const roots: OrgTreeNode[] = []
  organizations.value.forEach((o) => {
    const node = nodes.get(o.id)!
    if (o.parent_id && nodes.has(o.parent_id)) {
      const parent = nodes.get(o.parent_id)!
      if (!parent.children) parent.children = []
      parent.children.push(node)
    } else {
      roots.push(node)
    }
  })
  return roots
})

// 右侧用户：全部 或 按当前选中组织过滤
const filteredUsers = computed(() => {
  if (currentOrgId.value === null) return list.value
  return list.value.filter((u) => u.org_id === currentOrgId.value)
})

const currentOrgName = computed(() => {
  if (currentOrgId.value === null) return ''
  const org = organizations.value.find((o) => o.id === currentOrgId.value)
  return org ? org.name : ''
})

function orgName(id: number) {
  const org = organizations.value.find((o) => o.id === id)
  return org ? org.name : String(id)
}

async function load() {
  loading.value = true
  try {
    const [users, orgs, roles] = await Promise.all([listUsers(), listOrganizations(), listRoles()])
    list.value = users
    organizations.value = orgs
    allRoles.value = roles
  } finally {
    loading.value = false
  }
}

function selectAll() {
  currentOrgId.value = null
}

function onNodeClick(data: OrgTreeNode) {
  currentOrgId.value = data.id
}

function openCreate() {
  // 新增时默认继承当前选中组织；"全部用户"视图下则不预设
  form.value = {
    username: '',
    name: '',
    password: '',
    org_id: currentOrgId.value,
    status: 'ACTIVE',
  }
  dialogVisible.value = true
}

function openEdit(row: User) {
  form.value = { id: row.id, username: row.username, name: row.name, password: '', org_id: row.org_id, status: row.status }
  dialogVisible.value = true
}

async function onSave() {
  if (!form.value.username) {
    ElMessage.warning('请填写用户名')
    return
  }
  if (!form.value.id && !form.value.password) {
    ElMessage.warning('新增用户必须设置密码')
    return
  }
  try {
    if (form.value.id) {
      const data: Record<string, unknown> = {
        name: form.value.name,
        org_id: form.value.org_id,
        status: form.value.status,
      }
      if (form.value.password) data.password = form.value.password
      await updateUser(form.value.id, data)
    } else {
      await createUser({
        username: form.value.username,
        name: form.value.name,
        password: form.value.password,
        org_id: form.value.org_id,
        status: form.value.status,
      })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await load()
  } catch {
    // 拦截器已提示
  }
}

async function onDelete(row: User) {
  try {
    await ElMessageBox.confirm(`确认删除用户「${row.username}」？`, '提示', { type: 'warning' })
    await deleteUser(row.id)
    ElMessage.success('删除成功')
    await load()
  } catch {
    // 取消或失败
  }
}

async function openRoles(row: User) {
  roleUser.value = row
  roleVisible.value = true
  try {
    const roles = await getUserRoles(row.id)
    roleIds.value = roles.map((r) => r.id)
  } catch {
    // 拦截器已提示
  }
}

async function onSaveRoles() {
  if (!roleUser.value) return
  roleSaving.value = true
  try {
    await setUserRoles(roleUser.value.id, roleIds.value)
    ElMessage.success('角色已保存')
    roleVisible.value = false
  } catch {
    // 拦截器已提示
  } finally {
    roleSaving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text);
}
.page-sub {
  font-size: 13px;
  color: var(--color-text-secondary);
}
.user-layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.org-panel {
  width: 240px;
  flex-shrink: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 16px;
}
.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 12px;
}
.all-entry {
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
  transition: 0.15s;
}
.all-entry:hover {
  background: var(--color-tint);
  color: var(--color-primary);
}
.all-entry.active {
  background: var(--color-tint);
  color: var(--color-primary);
  font-weight: 600;
}
.org-tree {
  --el-tree-node-hover-bg-color: var(--color-tint);
}
.user-panel {
  flex: 1;
  min-width: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 16px;
}
.panel-sub {
  font-size: 12px;
  font-weight: 400;
  color: var(--color-text-secondary);
  margin-left: 12px;
}
.auth-section {
  margin-bottom: 24px;
}
.auth-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 12px;
}
.auth-footer {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
