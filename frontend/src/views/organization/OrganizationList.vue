<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">组织管理</div>
        <div class="page-sub">集团 / 水司 / 水厂 多级组织</div>
      </div>
      <el-button type="primary" @click="openCreate">新增组织</el-button>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="code" label="组织编码" width="140" />
      <el-table-column prop="name" label="组织名称" />
      <el-table-column prop="type" label="类型" width="120">
        <template #default="{ row }">
          <el-tag>{{ typeLabel(row.type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="上级组织" width="160">
        <template #default="{ row }">
          {{ row.parent_id ? parentName(row.parent_id) : '—' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑组织' : '新增组织'" width="480px">
      <el-form :model="form" label-width="90px" @submit.prevent>
        <el-form-item label="组织编码">
          <el-input v-model="form.code" />
        </el-form-item>
        <el-form-item label="组织名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.type" style="width: 100%">
            <el-option label="集团" value="GROUP" />
            <el-option label="水司" value="WATER_COMPANY" />
            <el-option label="营业所" value="BIZ_OFFICE" />
            <el-option label="水厂" value="PLANT" />
          </el-select>
        </el-form-item>
        <el-form-item label="上级组织">
          <el-select
            v-model="form.parent_id"
            placeholder="不选则为顶级组织"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="org in parentOptions"
              :key="org.id"
              :label="org.name"
              :value="org.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listOrganizations,
  createOrganization,
  updateOrganization,
  deleteOrganization,
  type Organization,
} from '@/api/organization'

const list = ref<Organization[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const form = ref<{
  id?: number
  code: string
  name: string
  type: string
  parent_id: number | null
  sort: number
}>({
  code: '',
  name: '',
  type: 'WATER_COMPANY',
  parent_id: null,
  sort: 0,
})

function typeLabel(type: string) {
  const map: Record<string, string> = {
    GROUP: '集团',
    WATER_COMPANY: '水司',
    BIZ_OFFICE: '营业所',
    PLANT: '水厂',
  }
  return map[type] ?? type
}

function parentName(id: number) {
  const org = list.value.find((o) => o.id === id)
  return org ? org.name : String(id)
}

// 上级组织候选：排除自身，避免自己成为自己的上级
const parentOptions = computed(() => {
  return list.value.filter((o) => o.id !== form.value.id)
})

async function load() {
  loading.value = true
  try {
    list.value = await listOrganizations()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = { code: '', name: '', type: 'WATER_COMPANY', parent_id: null, sort: 0 }
  dialogVisible.value = true
}

function openEdit(row: Organization) {
  form.value = {
    id: row.id,
    code: row.code,
    name: row.name,
    type: row.type,
    parent_id: row.parent_id,
    sort: row.sort,
  }
  dialogVisible.value = true
}

async function onSave() {
  if (!form.value.code || !form.value.name) {
    ElMessage.warning('请填写编码和名称')
    return
  }
  try {
    if (form.value.id) {
      await updateOrganization(form.value.id, {
        name: form.value.name,
        type: form.value.type,
        parent_id: form.value.parent_id,
        sort: form.value.sort,
      })
    } else {
      await createOrganization({
        code: form.value.code,
        name: form.value.name,
        type: form.value.type,
        parent_id: form.value.parent_id,
        sort: form.value.sort,
      })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await load()
  } catch {
    // 拦截器已提示
  }
}

async function onDelete(row: Organization) {
  try {
    await ElMessageBox.confirm(`确认删除组织「${row.name}」？`, '提示', { type: 'warning' })
    await deleteOrganization(row.id)
    ElMessage.success('删除成功')
    await load()
  } catch {
    // 取消或失败
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
</style>
