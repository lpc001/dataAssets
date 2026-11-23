<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">数据域</div>
        <div class="page-sub">维护数据域的名称、排序与边界说明；已有资产的域不能删除</div>
      </div>
      <div class="page-actions">
        <el-button :loading="loading" @click="load">刷新</el-button>
        <el-button type="primary" @click="openCreate">新增数据域</el-button>
      </div>
    </div>

    <div class="card table-card">
      <el-table :data="rows" v-loading="loading">
        <el-table-column label="域码" width="110">
          <template #default="{ row }"><span class="mono">{{ row.domain_code }}</span></template>
        </el-table-column>
        <el-table-column prop="domain_name" label="名称" min-width="140" />
        <el-table-column label="已登记资产" width="110" align="right">
          <template #default="{ row }">
            <span :class="{ zero: !row.asset_count }">{{ row.asset_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sort" label="排序" width="80" align="right" />
        <el-table-column prop="description" label="边界说明" min-width="260" show-overflow-tooltip />
        <el-table-column label="操作" width="150" align="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
            <el-tooltip :disabled="!row.asset_count" content="该域下已有资产，不能删除" placement="top">
              <span>
                <el-button size="small" text type="danger" :disabled="row.asset_count > 0" @click="onDelete(row)">
                  删除
                </el-button>
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑数据域' : '新增数据域'" width="520px">
      <el-form :model="form" label-width="90px" label-position="left">
        <el-form-item label="域码" required>
          <el-input v-model="form.domain_code" :disabled="!!form.id" placeholder="3-8 位小写字母，如 fin" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.domain_name" placeholder="如 财务" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" controls-position="right" />
        </el-form-item>
        <el-form-item label="边界说明">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="这个域管什么、不管什么" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createDomain, deleteDomain, listDomains, patchDomain, type Domain } from '@/api/catalog'

const rows = ref<Domain[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const form = reactive<any>({ id: 0, domain_code: '', domain_name: '', sort: 0, description: '' })

async function load() {
  loading.value = true
  try {
    rows.value = await listDomains()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, {
    id: 0,
    domain_code: '',
    domain_name: '',
    sort: (rows.value.length ? Math.max(...rows.value.map((r) => r.sort)) : 0) + 1,
    description: '',
  })
  dialogVisible.value = true
}

function openEdit(row: Domain) {
  Object.assign(form, {
    id: row.id,
    domain_code: row.domain_code,
    domain_name: row.domain_name,
    sort: row.sort,
    description: row.description || '',
  })
  dialogVisible.value = true
}

async function onSave() {
  if (!form.domain_name || !form.domain_code) {
    ElMessage.warning('请填写域码与名称')
    return
  }
  saving.value = true
  try {
    if (form.id) {
      await patchDomain(form.id, {
        domain_name: form.domain_name,
        sort: form.sort,
        description: form.description || null,
      })
      ElMessage.success('已保存')
    } else {
      await createDomain({
        domain_code: form.domain_code.trim().toLowerCase(),
        domain_name: form.domain_name,
        sort: form.sort,
        description: form.description || null,
      })
      ElMessage.success('已新增')
    }
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function onDelete(row: Domain) {
  await ElMessageBox.confirm(
    `确认删除数据域「${row.domain_name}」（${row.domain_code}）？`,
    '删除确认',
    { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' },
  )
  await deleteDomain(row.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<style scoped>
.table-card {
  padding: 6px 4px;
  overflow: hidden;
}
.zero {
  color: var(--color-text-secondary);
}
</style>
