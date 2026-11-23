<template>
  <div v-loading="loading" class="sample">
    <div class="hint">
      只读抽样：显示前 {{ limit }} 行
      <span v-if="data"> · {{ data.schema_name }}.{{ data.table_name }}（共 {{ data.rows.length }} 行返回）</span>
    </div>
    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />
    <template v-else>
      <el-table :data="rows" size="small" max-height="380" border>
        <el-table-column
          v-for="(col, index) in columns"
          :key="col"
          :label="col"
          min-width="130"
          show-overflow-tooltip
        >
          <template #default="{ row }">{{ row[index] === null ? '—' : row[index] }}</template>
        </el-table-column>
      </el-table>
      <div v-if="data && !data.rows.length" class="empty">该表当前没有数据</div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { PreviewData } from '@/api/catalog'

const props = withDefaults(
  defineProps<{ fetcher: () => Promise<PreviewData>; limit?: number }>(),
  { limit: 20 },
)

const loading = ref(false)
const error = ref('')
const data = ref<PreviewData | null>(null)
const columns = ref<string[]>([])
const rows = ref<PreviewData['rows']>([])

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await props.fetcher()
    columns.value = data.value.columns
    rows.value = data.value.rows
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '读取示例数据失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.sample {
  min-height: 120px;
}
.hint {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 10px;
}
.empty {
  padding: 24px 0;
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 13px;
}
</style>
