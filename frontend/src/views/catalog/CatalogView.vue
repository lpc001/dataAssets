<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">资产目录</div>
        <div class="page-sub">已登记发布的数据资产（1 个资产对应 1 张资源表）</div>
      </div>
      <div class="summary">
        <span>资产 {{ summary.asset_count }}</span>
        <span>资源 {{ summary.resource_count }}</span>
        <span>域 {{ summary.domain_count }}</span>
      </div>
    </div>

    <div class="catalog-body">
      <aside class="domain-panel">
        <div
          class="domain-item"
          :class="{ active: !filters.domain_code && !filters.group_type }"
          @click="pickDomain('')"
        >
          全部数据域
        </div>
        <div class="domain-item" :class="{ active: filters.group_type === 'PUBLIC' }" @click="pickGroup('PUBLIC')">
          <span>公共维度</span>
          <span class="code">跨域共享</span>
        </div>
        <div class="domain-item" :class="{ active: filters.group_type === 'TOPIC' }" @click="pickGroup('TOPIC')">
          <span>跨域专题</span>
          <span class="code">产销差等</span>
        </div>
        <div class="domain-item" :class="{ active: filters.group_type === 'OTHER' }" @click="pickGroup('OTHER')">
          <span>未归类</span>
          <span class="code">待分配</span>
        </div>
        <div class="divider" />
        <div
          v-for="d in domains"
          :key="d.domain_code"
          class="domain-item"
          :class="{ active: filters.domain_code === d.domain_code && filters.group_type === 'DOMAIN' }"
          @click="pickDomain(d.domain_code)"
        >
          <span>{{ d.domain_name }}</span>
          <span class="code">{{ d.domain_code }}</span>
        </div>
      </aside>

      <section class="table-panel">
        <div class="filters">
          <el-select v-model="filters.layer" placeholder="全部数据类型" clearable style="width: 150px" @change="onLayerChange">
            <el-option label="维度数据" value="DIM" />
            <el-option label="业务数据" value="DWD" />
            <el-option label="汇总统计" value="DWS" />
          </el-select>
          <el-select v-model="filters.status" placeholder="全部状态" style="width: 130px" @change="reload">
            <el-option label="已发布" value="PUBLISHED" />
            <el-option label="草稿" value="DRAFT" />
            <el-option label="已下线" value="OFFLINE" />
            <el-option label="全部" value="" />
          </el-select>
          <el-input v-model="filters.keyword" placeholder="资产名 / 编码 / 表名" clearable style="width: 220px" @keyup.enter="reload" />
          <el-button type="primary" @click="reload">查询</el-button>
        </div>

        <el-table :data="rows" class="card table-card" v-loading="loading" @row-click="openDetail">
          <el-table-column label="域 / 归类" width="130">
            <template #default="{ row }">
              {{ row.group_type && row.group_type !== 'DOMAIN' ? GROUP_LABELS[row.group_type] || row.group_type : domainName(row.domain_code) }}
            </template>
          </el-table-column>
          <el-table-column prop="asset_code" label="资产编码" width="110">
            <template #default="{ row }"><span class="mono">{{ row.asset_code || '—' }}</span></template>
          </el-table-column>
          <el-table-column label="资产名称" min-width="200">
            <template #default="{ row }">{{ row.asset_name }}</template>
          </el-table-column>
          <el-table-column label="来源表" min-width="220">
            <template #default="{ row }">
              <span class="mono">{{ row.table_name }}</span>
              <span class="schema">{{ row.schema_name }}</span>
            </template>
          </el-table-column>
          <el-table-column label="数据类型" width="110">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ layerLabel(row.data_layer) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'PUBLISHED' ? 'success' : 'info'">
                {{ statusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="row_count" label="行数" width="90" align="right" />
          <el-table-column label="操作" width="140" align="right">
            <template #default="{ row }">
              <el-button size="small" text @click.stop="openDetail(row)">查看</el-button>
              <el-button
                v-if="row.status === 'PUBLISHED'"
                size="small"
                text
                type="warning"
                @click.stop="toggleStatus(row, 'OFFLINE')"
              >
                下架
              </el-button>
              <el-button v-else size="small" text type="success" @click.stop="toggleStatus(row, 'PUBLISHED')">
                发布
              </el-button>
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
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { assetSummary, listAssets, listDomains, patchAsset, type Asset, type Domain } from '@/api/catalog'

const router = useRouter()
const domains = ref<Domain[]>([])
const rows = ref<Asset[]>([])
const total = ref(0)
const loading = ref(false)
const summary = reactive({
  datasource_count: 0,
  resource_count: 0,
  asset_count: 0,
  column_count: 0,
  domain_count: 0,
  missing_count: 0,
})

const filters = reactive({
  domain_code: '',
  group_type: '',
  layer: '',
  status: 'PUBLISHED',
  keyword: '',
  page: 1,
  page_size: 20,
})

const GROUP_LABELS: Record<string, string> = {
  PUBLIC: '公共维度',
  TOPIC: '跨域专题',
  OTHER: '未归类',
}

const STATUS_LABELS: Record<string, string> = { PUBLISHED: '已发布', DRAFT: '草稿', OFFLINE: '已下线' }

function statusLabel(status: string) {
  return STATUS_LABELS[status] || status
}

const LAYER_LABELS: Record<string, string> = {
  DIM: '维度数据',
  DWD: '业务数据',
  DWS: '汇总统计',
  OTHER: '其他',
}

function layerLabel(layer: string | null) {
  return layer ? LAYER_LABELS[layer] || layer : '—'
}

function domainName(code: string | null) {
  if (!code) return '公共'
  return domains.value.find((d) => d.domain_code === code)?.domain_name || code
}

async function loadSummary() {
  Object.assign(summary, await assetSummary())
}

async function reload() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: filters.page, page_size: filters.page_size }
    if (filters.domain_code) params.domain_code = filters.domain_code
    if (filters.group_type) params.group_type = filters.group_type
    if (filters.layer) params.layer = filters.layer
    if (filters.status) params.status = filters.status
    if (filters.keyword) params.keyword = filters.keyword
    const res = await listAssets(params)
    rows.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function pickGroup(group: string) {
  filters.group_type = group
  filters.domain_code = ''
  filters.layer = ''
  filters.page = 1
  reload()
}

function pickDomain(code: string) {
  filters.group_type = code ? 'DOMAIN' : ''
  filters.domain_code = code
  filters.layer = ''
  filters.page = 1
  reload()
}

function onLayerChange() {
  filters.page = 1
  reload()
}

function onPage(page: number) {
  filters.page = page
  reload()
}

function openDetail(row: Asset) {
  router.push(`/catalog/${row.id}`)
}

async function toggleStatus(row: Asset, target: 'OFFLINE' | 'PUBLISHED') {
  const label = target === 'OFFLINE' ? '下架' : '发布'
  await ElMessageBox.confirm(
    target === 'OFFLINE'
      ? `确认下架「${row.asset_name}」（${row.asset_code}）？下架后将不在资产目录显示，但数据与血缘保留。`
      : `确认重新发布「${row.asset_name}」？`,
    `${label}确认`,
    { type: 'warning', confirmButtonText: `确认${label}`, cancelButtonText: '取消' },
  )
  await patchAsset(row.id, { status: target })
  ElMessage.success(`已${label}`)
  await reload()
}

onMounted(async () => {
  domains.value = await listDomains()
  await Promise.all([reload(), loadSummary()])
})
</script>

<style scoped>
.summary {
  display: flex;
  gap: 16px;
  color: var(--color-text-secondary);
  font-size: 13px;
}
.catalog-body {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.domain-panel {
  width: 230px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  padding: 8px;
  flex-shrink: 0;
}
.domain-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
}
.domain-item:hover {
  background: var(--color-tint);
}
.domain-item.active {
  background: var(--color-tint);
  color: var(--color-primary);
  font-weight: 600;
}
.domain-item .code {
  color: var(--color-text-secondary);
  font-size: 12px;
}
.divider {
  height: 1px;
  background: var(--color-border);
  margin: 6px 8px;
}
.table-panel {
  flex: 1;
  min-width: 0;
}
.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}
.table-card {
  overflow: hidden;
}
.schema {
  margin-left: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.pager {
  margin-top: 12px;
  justify-content: flex-end;
}
</style>
