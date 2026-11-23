<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">角色管理</div>
        <div class="page-sub">角色、用户分配与数据权限</div>
      </div>
      <el-button type="primary" @click="openCreate">新增角色</el-button>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="code" label="角色编码" width="140" />
      <el-table-column prop="name" label="角色名称" width="150" />
      <el-table-column prop="description" label="描述" />
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="primary" @click="openAuth(row)">授权</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑角色' : '新增角色'" width="480px">
      <el-form :model="form" label-width="90px" @submit.prevent>
        <el-form-item label="角色编码">
          <el-input v-model="form.code" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item label="角色名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 授权抽屉 -->
    <el-drawer v-model="authVisible" :title="`授权：${authRole?.name ?? ''}`" size="520px">
      <div class="auth-section">
        <div class="auth-title">分配用户</div>
        <el-select
          v-model="authUserIds"
          multiple
          filterable
          placeholder="选择拥有该角色的用户"
          style="width: 100%"
        >
          <el-option v-for="u in allUsers" :key="u.id" :label="u.name || u.username" :value="u.id" />
        </el-select>
      </div>

      <div class="auth-section">
        <div class="auth-title">功能权限</div>
        <div v-if="isAdminRole" class="perm-hint admin-hint">
          管理员角色默认拥有全部权限，无需逐项勾选。
        </div>
        <div v-else class="perm-hint">
          不勾选的模块在该角色下不显示、也不能调用。完全不勾选时，只有「指标查看」和「修改自己的资料」。
        </div>
        <div v-for="g in permGroups" :key="g.name" class="perm-group">
          <div class="perm-group-name">{{ g.name }}</div>
          <el-checkbox-group v-model="authPerms" :disabled="isAdminRole">
            <el-checkbox v-for="p in g.items" :key="p.code" :value="p.code">{{ p.name }}</el-checkbox>
          </el-checkbox-group>
        </div>
      </div>

      <div class="auth-section">
        <div class="auth-title">数据权限范围</div>
        <el-radio-group v-model="authScope" class="scope-group">
          <el-radio value="ALL">全部组织</el-radio>
          <el-radio value="ORG_AND_CHILD">本级及下级</el-radio>
          <el-radio value="ORG_ONLY">仅本级</el-radio>
          <el-radio value="CUSTOM">自定义组织</el-radio>
        </el-radio-group>
        <el-tree-select
          v-if="authScope === 'CUSTOM'"
          v-model="authCustomOrgs"
          :data="orgTree"
          :props="{ label: 'name', children: 'children' }"
          node-key="id"
          multiple
          show-checkbox
          check-strictly
          clearable
          placeholder="选择可见的组织"
          style="width: 100%; margin-top: 12px"
        />
      </div>

      <div class="auth-footer">
        <el-button type="primary" :loading="authSaving" @click="onSaveAuth">保存授权</el-button>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listRoles,
  createRole,
  updateRole,
  deleteRole,
  getRoleDataScope,
  setRoleDataScope,
  listRoleUsers,
  setRoleUsers,
  getRolePermissions,
  setRolePermissions,
  getPermissionCatalog,
  type Role,
  type PermissionItem,
} from '@/api/role'
import { listUsers, type User } from '@/api/user'
import { listOrganizations, type Organization } from '@/api/organization'

interface OrgTreeNode {
  id: number
  name: string
  children?: OrgTreeNode[]
}

const list = ref<Role[]>([])
const allUsers = ref<User[]>([])
const organizations = ref<Organization[]>([])
const loading = ref(false)

const dialogVisible = ref(false)
const form = ref<{ id?: number; code: string; name: string; description: string }>({
  code: '',
  name: '',
  description: '',
})

const authVisible = ref(false)
const authRole = ref<Role | null>(null)
const authPerms = ref<string[]>([])
const isAdminRole = computed(() => authRole.value?.code === 'ADMIN')
const permissionCatalog = ref<PermissionItem[]>([])

const permGroups = computed(() => {
  const groups: { name: string; items: PermissionItem[] }[] = []
  for (const p of permissionCatalog.value) {
    let g = groups.find((x) => x.name === p.group)
    if (!g) {
      g = { name: p.group, items: [] }
      groups.push(g)
    }
    g.items.push(p)
  }
  return groups
})
const authUserIds = ref<number[]>([])
const authScope = ref('ALL')
const authCustomOrgs = ref<number[]>([])
const authSaving = ref(false)

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

async function load() {
  loading.value = true
  try {
    const [roles, users, orgs] = await Promise.all([
      listRoles(),
      listUsers(),
      listOrganizations(),
    ])
    list.value = roles
    allUsers.value = users
    organizations.value = orgs
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = { code: '', name: '', description: '' }
  dialogVisible.value = true
}

function openEdit(row: Role) {
  form.value = { id: row.id, code: row.code, name: row.name, description: row.description }
  dialogVisible.value = true
}

async function onSave() {
  if (!form.value.code || !form.value.name) {
    ElMessage.warning('请填写编码和名称')
    return
  }
  try {
    if (form.value.id) {
      await updateRole(form.value.id, { name: form.value.name, description: form.value.description })
    } else {
      await createRole({ code: form.value.code, name: form.value.name, description: form.value.description })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await load()
  } catch {
    // 拦截器已提示
  }
}

async function onDelete(row: Role) {
  try {
    await ElMessageBox.confirm(`确认删除角色「${row.name}」？`, '提示', { type: 'warning' })
    await deleteRole(row.id)
    ElMessage.success('删除成功')
    await load()
  } catch {
    // 取消或失败
  }
}

async function openAuth(row: Role) {
  authRole.value = row
  authVisible.value = true
  try {
    const [users, scope, perms, catalog] = await Promise.all([
      listRoleUsers(row.id),
      getRoleDataScope(row.id),
      getRolePermissions(row.id),
      getPermissionCatalog(),
    ])
    if (!permissionCatalog.value.length) permissionCatalog.value = catalog
    authPerms.value = [...perms.permissions]
    authUserIds.value = users.map((u) => u.id)
    authScope.value = scope.scope_type
    authCustomOrgs.value = scope.custom_org_ids
      ? scope.custom_org_ids.split(',').map((s) => Number(s))
      : []
  } catch {
    // 拦截器已提示
  }
}

async function onSaveAuth() {
  if (!authRole.value) return
  authSaving.value = true
  try {
    await setRoleUsers(authRole.value.id, authUserIds.value)
    await setRolePermissions(authRole.value.id, authPerms.value)
    await setRoleDataScope(authRole.value.id, {
      scope_type: authScope.value,
      custom_org_ids: authScope.value === 'CUSTOM' ? authCustomOrgs.value : [],
    })
    ElMessage.success('授权已保存')
    authVisible.value = false
  } catch {
    // 拦截器已提示
  } finally {
    authSaving.value = false
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
.auth-section {
  margin-bottom: 24px;
}
.auth-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 12px;
}
.scope-group {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}
.perm-hint {
  font-size: 12px;
  color: #6b8299;
  line-height: 1.6;
  margin-bottom: 12px;
}
.admin-hint {
  color: #0a84ff;
}
.perm-group {
  margin-bottom: 10px;
}
.perm-group-name {
  font-size: 12px;
  color: #0f2b46;
  font-weight: 600;
  margin-bottom: 4px;
}
.auth-footer {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
