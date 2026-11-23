<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">指标中心</div>
        <div class="page-sub">指标从资产字段长出，校验通过后发布；台账在 data_assets 内以视图提供</div>
      </div>
      <div class="page-actions">
        <el-button :loading="loading" @click="reload">刷新</el-button>
        <el-button type="primary" @click="$router.push('/indicators/new')">新建指标</el-button>
      </div>
    </div>

    <div class="card table-card">
      <div class="filters">
        <el-select v-model="filters.domain_code" placeholder="全部数据域" clearable style="width: 160px" @change="reload">
          <el-option v-for="d in domains" :key="d.domain_code" :label="d.domain_name" :value="d.domain_code" />
        </el-select>
        <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 130px" @change="reload">
          <el-option label="草稿" value="DRAFT" />
          <el-option label="已发布" value="PUBLISHED" />
          <el-option label="已废止" value="RETIRED" />
        </el-select>
        <el-input v-model="filters.keyword" placeholder="编码 / 名称" clearable style="width: 200px" @keyup.enter="reload" />
        <el-button type="primary" @click="reload">查询</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" @row-click="openDetail">
        <el-table-column label="指标编码" width="120">
          <template #default="{ row }"><span class="mono">{{ row.indicator_code }}</span></template>
        </el-table-column>
        <el-table-column prop="indicator_name" label="指标名称" min-width="150" />
        <el-table-column label="域" width="110">
          <template #default="{ row }">{{ domainName(row.domain_code) }}</template>
        </el-table-column>
        <el-table-column label="取数路径" min-width="240">
          <template #default="{ row }">
            <span v-if="row.source_path" class="mono path">{{ row.source_path.table_name }}.{{ row.source_path.column_name }}</span>
            <el-tag v-else size="small" type="danger" effect="plain">未挂载</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="校验" width="140">
          <template #default="{ row }">
            <el-tag v-if="row.validation.block" size="small" type="danger">{{ row.validation.block }} 阻断</el-tag>
            <el-tag v-else size="small" type="success">通过</el-tag>
            <el-tag v-if="row.validation.warn" size="small" type="warning" style="margin-left: 4px">{{ row.validation.warn }} 警告</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click.stop="openDetail(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pager"
        layout="total, prev, pager, next"
        :total="total"
        :page-size="filters.page_size"
        :current-page="filters.page"
        @current-change="onPage"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listDomains, type Domain } from '@/api/catalog'
import { listIndicators, type Indicator } from '@/api/indicator'

const router = useRouter()
const domains = ref<Domain[]>([])
const rows = ref<Indicator[]>([])
const total = ref(0)
const loading = ref(false)

const filters = reactive({
  domain_code: '',
  status: '',
  keyword: '',
  page: 1,
  page_size: 50,
})

const STATUS_LABELS: Record<string, string> = { DRAFT: '草稿', PUBLISHED: '已发布', RETIRED: '已废止' }

function statusLabel(status: string) {
  return STATUS_LABELS[status] || status
}

function statusType(status: string) {
  return status === 'PUBLISHED' ? 'success' : status === 'RETIRED' ? 'info' : 'warning'
}

function domainName(code: string | null) {
  if (!code) return '公共'
  return domains.value.find((d) => d.domain_code === code)?.domain_name || code
}

async function reload() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: filters.page, page_size: filters.page_size }
    if (filters.domain_code) params.domain_code = filters.domain_code
    if (filters.status) params.status = filters.status
    if (filters.keyword) params.keyword = filters.keyword
    const res = await listIndicators(params)
    rows.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onPage(page: number) {
  filters.page = page
  reload()
}

function openDetail(row: Indicator) {
  router.push(`/indicators/${row.id}`)
}

onMounted(async () => {
  domains.value = await listDomains()
  await reload()
})
</script>

<style scoped>
.table-card {
  padding: 14px 16px;
}
.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.path {
  color: var(--color-text-secondary);
}
.pager {
  margin-top: 12px;
  justify-content: flex-end;
}
</style>
