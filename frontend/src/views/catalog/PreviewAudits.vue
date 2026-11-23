<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">预览审计</div>
        <div class="page-sub">记录谁在什么时候查看了哪张表的哪些字段，以及是否脱敏</div>
      </div>
      <div class="page-actions">
        <el-button :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <div class="card table-card">
      <el-table :data="rows" v-loading="loading">
        <el-table-column label="时间" width="170">
          <template #default="{ row }"><span class="time">{{ fmt(row.created_at) }}</span></template>
        </el-table-column>
        <el-table-column prop="username" label="操作人" width="110" />
        <el-table-column label="对象" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.object_type === 'ASSET' ? '资产' : '资源' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="表" min-width="200">
          <template #default="{ row }">
            <span class="mono">{{ row.table_name }}</span>
            <span class="schema">{{ row.schema_name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="columns_text" label="查询字段" min-width="220" show-overflow-tooltip />
        <el-table-column label="行数" width="100" align="right">
          <template #default="{ row }">{{ row.row_returned }} / {{ row.row_limit }}</template>
        </el-table-column>
        <el-table-column label="脱敏" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.masked ? 'success' : 'warning'">{{ row.masked ? '已脱敏' : '明文' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="client_ip" label="来源 IP" width="130" />
      </el-table>
      <el-empty v-if="!loading && !rows.length" description="还没有预览记录" :image-size="80" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listPreviewAudits, type PreviewAudit } from '@/api/catalog'

const rows = ref<PreviewAudit[]>([])
const loading = ref(false)

function fmt(value: string) {
  return value ? value.replace('T', ' ').slice(0, 19) : '—'
}

async function load() {
  loading.value = true
  try {
    rows.value = await listPreviewAudits(200)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.table-card {
  padding: 6px 4px;
  overflow: hidden;
}
.time {
  color: var(--color-text-secondary);
  font-size: 12.5px;
}
.schema {
  margin-left: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
</style>
