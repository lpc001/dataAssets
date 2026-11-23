<template>
  <div class="sample">
    <div class="toolbar">
      <div class="tool-item">
        <span class="label">行数</span>
        <el-select v-model="limit" style="width: 96px" @change="reload">
          <el-option :value="10" label="10 行" />
          <el-option :value="20" label="20 行" />
          <el-option :value="50" label="50 行" />
          <el-option :value="100" label="100 行" />
        </el-select>
      </div>
      <div class="tool-item grow">
        <span class="label">字段</span>
        <el-select
          v-model="selected"
          multiple
          collapse-tags
          collapse-tags-tooltip
          clearable
          placeholder="全部字段"
          style="width: 100%"
          :disabled="!allColumns.length"
          @change="reload"
        >
          <el-option v-for="c in allColumns" :key="c" :label="c" :value="c" />
        </el-select>
      </div>
      <div class="tool-item" v-if="canRaw">
        <span class="label">明文</span>
        <el-switch v-model="raw" @change="reload" />
      </div>
      <el-button :loading="loading" @click="reload">刷新</el-button>
    </div>

    <div class="hint">
      只读抽样 · 最多 {{ limit }} 行
      <span v-if="data"> · {{ data.schema_name }}.{{ data.table_name }}（实返 {{ data.rows.length }} 行）</span>
      <span v-if="data && data.masked_columns.length" class="masked">
        · 已脱敏：{{ data.masked_columns.join('、') }}
      </span>
    </div>

    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />
    <template v-else>
      <el-table :data="rows" size="small" max-height="400" border v-loading="loading">
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
      <div v-if="data && !rows.length" class="empty">该表当前没有数据</div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import type { PreviewData, PreviewQuery } from '@/api/catalog'

const props = withDefaults(
  defineProps<{ fetcher: (q: PreviewQuery) => Promise<PreviewData> }>(),
  {},
)

const auth = useAuthStore()
const canRaw = auth.hasPerm('ast:preview:raw')

const loading = ref(false)
const error = ref('')
const data = ref<PreviewData | null>(null)
const columns = ref<string[]>([])
const rows = ref<PreviewData['rows']>([])
const allColumns = ref<string[]>([])
const limit = ref(20)
const raw = ref(false)
const selected = ref<string[]>([])

async function reload() {
  loading.value = true
  error.value = ''
  try {
    data.value = await props.fetcher({
      limit: limit.value,
      raw: raw.value,
      columns: selected.value.length ? selected.value : undefined,
    })
    columns.value = data.value.columns
    rows.value = data.value.rows
    allColumns.value = data.value.all_columns
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '读取示例数据失败'
  } finally {
    loading.value = false
  }
}

onMounted(reload)
</script>

<style scoped>
.sample {
  min-height: 140px;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.tool-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.tool-item.grow {
  flex: 1;
  min-width: 240px;
}
.label {
  font-size: 12.5px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}
.hint {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 10px;
}
.masked {
  color: var(--color-warning);
}
.empty {
  padding: 24px 0;
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 13px;
}
</style>
