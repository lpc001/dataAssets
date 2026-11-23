<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">资源池</div>
        <div class="page-sub">数据源采集到的技术元数据；勾选后确认登记，才会进入资产目录</div>
      </div>
      <div class="page-actions">
        <el-button :loading="loading" @click="reload">刷新</el-button>
        <el-button type="primary" :disabled="!selection.length" @click="openRegister(selection)">
          登记为资产{{ selection.length ? `（${selection.length}）` : '' }}
        </el-button>
      </div>
    </div>

    <div class="stat-row">
      <div class="stat"><div class="stat-value">{{ summary.resource_count }}</div><div class="stat-label">资源总数</div></div>
      <div class="stat"><div class="stat-value">{{ summary.asset_count }}</div><div class="stat-label">已登记资产</div></div>
      <div class="stat"><div class="stat-value">{{ unregistered }}</div><div class="stat-label">待登记</div></div>
      <div class="stat"><div class="stat-value">{{ summary.missing_count }}</div><div class="stat-label">远端已消失</div></div>
    </div>

    <div class="card list-card">
      <div class="filters">
        <el-select v-model="filters.datasource_id" placeholder="全部数据源" clearable style="width: 200px" @change="reload">
          <el-option v-for="d in datasources" :key="d.id" :label="d.name" :value="d.id" />
        </el-select>
        <el-select v-model="filters.registered" placeholder="全部状态" clearable style="width: 140px" @change="reload">
          <el-option label="待登记" :value="false" />
          <el-option label="已登记" :value="true" />
        </el-select>
        <el-select v-model="filters.kind" placeholder="全部对象" clearable style="width: 120px" @change="reload">
          <el-option label="表" value="TABLE" />
          <el-option label="视图" value="VIEW" />
        </el-select>
        <el-input v-model="filters.keyword" placeholder="表名 / 注释" clearable style="width: 200px" @keyup.enter="reload" />
        <el-button type="primary" @click="reload">查询</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" @selection-change="onSelect">
        <el-table-column type="selection" width="46" :selectable="(row: ResourceTable) => !row.registered" />
        <el-table-column label="表名" min-width="230">
          <template #default="{ row }">
            <div class="tname mono link" @click="openDetail(row)">{{ row.table_name }}</div>
            <div class="tcomment">{{ row.table_comment || '—' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="schema_name" label="Schema" width="100" />
        <el-table-column label="对象" width="150">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.table_kind }}</el-tag>
            <el-tag v-if="row.is_system" size="small" type="info" class="ml">系统表</el-tag>
            <el-tag v-if="row.is_temp" size="small" type="warning" class="ml">临时/备份</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="建议归属" width="140">
          <template #default="{ row }">
            <span class="suggest">{{ layerLabel(row.suggested_layer) }}</span>
            <span class="suggest-sub">{{ domainLabel(row.suggested_domain) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="row_count" label="行数" width="90" align="right" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <span class="status">
              <i class="dot" :class="row.registered ? 'ok' : 'idle'" />
              {{ row.registered ? '已登记' : '待登记' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" v-if="!row.registered" @click="openRegister([row])">登记</el-button>
            <el-button size="small" text @click="openDetail(row)">查看</el-button>
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

    <el-drawer v-model="detailVisible" :title="detail ? detail.table_name : '资源详情'" size="760px">
      <template v-if="detail">
        <div class="d-head">
          <span class="mono">{{ detail.schema_name }}.{{ detail.table_name }}</span>
          <el-tag size="small" :type="detail.registered ? 'success' : 'info'">
            {{ detail.registered ? '已登记资产' : '待登记' }}
          </el-tag>
          <el-tag v-if="detail.is_system" size="small" type="info">系统表</el-tag>
          <el-tag v-if="detail.is_temp" size="small" type="warning">临时/备份</el-tag>
        </div>

        <el-descriptions :column="3" border size="small" class="d-desc">
          <el-descriptions-item label="表注释" :span="3">{{ detail.table_comment || '—' }}</el-descriptions-item>
          <el-descriptions-item label="对象类型">{{ detail.table_kind }}</el-descriptions-item>
          <el-descriptions-item label="行数">{{ detail.row_count ?? '—' }}</el-descriptions-item>
          <el-descriptions-item label="字段数">{{ detail.columns.length }}</el-descriptions-item>
          <el-descriptions-item label="建议数据类型">{{ layerLabel(detail.suggested_layer) }}</el-descriptions-item>
          <el-descriptions-item label="建议归属域">{{ domainLabel(detail.suggested_domain) }}</el-descriptions-item>
          <el-descriptions-item label="远端状态">{{ detail.remote_status === 'ACTIVE' ? '在库' : '已消失' }}</el-descriptions-item>
        </el-descriptions>

        <div class="d-sub">字段清单（{{ detail.columns.length }}）</div>
        <el-table :data="detail.columns" size="small" max-height="380">
          <el-table-column prop="ordinal" label="#" width="50" />
          <el-table-column prop="column_name" label="字段" min-width="170">
            <template #default="{ row }"><span class="mono">{{ row.column_name }}</span></template>
          </el-table-column>
          <el-table-column prop="data_type" label="类型" width="120" />
          <el-table-column prop="column_comment" label="注释" min-width="180" show-overflow-tooltip />
          <el-table-column label="标记" width="110">
            <template #default="{ row }">
              <el-tag v-if="row.is_primary_key" size="small" type="warning">PK</el-tag>
              <el-tag v-if="row.is_partition_key" size="small" type="info">分区</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </template>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button
          v-if="detail && detail.asset_id"
          type="primary"
          @click="$router.push(`/catalog/${detail.asset_id}`)"
        >
          打开资产详情
        </el-button>
        <el-button v-else-if="detail" type="primary" @click="openRegister([detail])">登记为资产</el-button>
      </template>
    </el-drawer>

    <el-dialog v-model="registerVisible" :title="isBatch ? `登记为资产（${pending.length} 项）` : '登记为资产'" width="620px">
      <div class="reg-hint">登记后会立即发布到资产目录，可在资产详情里修改或下架。</div>

      <el-form v-if="!isBatch && pending[0]" :model="regForm" label-width="96px" label-position="left">
        <el-form-item label="来源表">
          <span class="mono">{{ pending[0].schema_name }}.{{ pending[0].table_name }}</span>
        </el-form-item>
        <el-form-item label="资产名称">
          <el-input v-model="regForm.asset_name" />
        </el-form-item>
        <el-form-item label="所属数据域">
          <el-select v-model="regForm.domain_code" clearable style="width: 240px" placeholder="公共/跨域可不选">
            <el-option v-for="d in domains" :key="d.domain_code" :label="d.domain_name" :value="d.domain_code" />
          </el-select>
        </el-form-item>
        <el-form-item label="追溯档">
          <el-select v-model="regForm.trace_level" clearable style="width: 180px" placeholder="按规则建议">
            <el-option label="A 逐条对账" value="A" />
            <el-option label="B 事件流" value="B" />
            <el-option label="C 主数据" value="C" />
            <el-option label="D 汇总" value="D" />
          </el-select>
        </el-form-item>
        <el-form-item label="责任人">
          <el-input v-model="regForm.owner_name" placeholder="选填" />
        </el-form-item>
      </el-form>

      <template v-else>
        <el-table :data="pending" size="small" max-height="260">
          <el-table-column prop="table_name" label="表名" min-width="180">
            <template #default="{ row }"><span class="mono">{{ row.table_name }}</span></template>
          </el-table-column>
          <el-table-column label="注释" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">{{ row.table_comment || '—' }}</template>
          </el-table-column>
          <el-table-column label="建议归属" width="130">
            <template #default="{ row }">
              {{ layerLabel(row.suggested_layer) }} / {{ domainLabel(row.suggested_domain) }}
            </template>
          </el-table-column>
        </el-table>
        <el-form label-width="96px" label-position="left" class="batch-form">
          <el-form-item label="统一归属域">
            <el-select v-model="regForm.domain_code" clearable style="width: 240px" placeholder="不选则按各自建议">
              <el-option v-for="d in domains" :key="d.domain_code" :label="d.domain_name" :value="d.domain_code" />
            </el-select>
          </el-form-item>
          <el-form-item label="责任人">
            <el-input v-model="regForm.owner_name" placeholder="选填" />
          </el-form-item>
        </el-form>
      </template>

      <template #footer>
        <el-button @click="registerVisible = false">取消</el-button>
        <el-button type="primary" :loading="registering" @click="submitRegister">
          确认登记
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  assetSummary,
  getResource,
  listDomains,
  listResources,
  registerAssets,
  type Domain,
  type RegisterItem,
  type ResourceDetail,
  type ResourceTable,
} from '@/api/catalog'
import { listDatasources, type DataSource } from '@/api/datasource'

const rows = ref<ResourceTable[]>([])
const total = ref(0)
const loading = ref(false)
const datasources = ref<DataSource[]>([])
const domains = ref<Domain[]>([])
const selection = ref<ResourceTable[]>([])
const detailVisible = ref(false)
const detail = ref<ResourceDetail | null>(null)
const registerVisible = ref(false)
const registering = ref(false)
const pending = ref<ResourceTable[]>([])
const summary = reactive({
  datasource_count: 0,
  resource_count: 0,
  asset_count: 0,
  column_count: 0,
  domain_count: 0,
  missing_count: 0,
})

const regForm = reactive({
  asset_name: '',
  domain_code: '' as string | null,
  trace_level: '' as string | null,
  owner_name: '',
})

const filters = reactive({
  datasource_id: null as number | null,
  registered: null as boolean | null,
  kind: '',
  keyword: '',
  page: 1,
  page_size: 20,
})

const unregistered = computed(() => Math.max(summary.resource_count - summary.asset_count, 0))
const isBatch = computed(() => pending.value.length > 1)

const LAYER_LABELS: Record<string, string> = {
  DIM: '维度数据',
  DWD: '业务数据',
  DWS: '汇总统计',
  OTHER: '其他',
}

function layerLabel(layer: string | null) {
  return layer ? LAYER_LABELS[layer] || layer : '其他'
}

function domainLabel(code: string | null) {
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
    if (filters.datasource_id) params.datasource_id = filters.datasource_id
    if (filters.registered !== null) params.registered = filters.registered
    if (filters.kind) params.kind = filters.kind
    if (filters.keyword) params.keyword = filters.keyword
    const res = await listResources(params)
    rows.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onSelect(items: ResourceTable[]) {
  selection.value = items
}

function onPage(page: number) {
  filters.page = page
  reload()
}

function openRegister(items: ResourceTable[]) {
  const targets = items.filter((i) => !i.registered)
  if (!targets.length) {
    ElMessage.warning('所选资源都已登记')
    return
  }
  pending.value = targets
  Object.assign(regForm, {
    asset_name: targets[0].table_comment || targets[0].table_name,
    domain_code: isBatch.value ? null : targets[0].suggested_domain,
    trace_level: isBatch.value ? null : targets[0].suggested_trace,
    owner_name: '',
  })
  registerVisible.value = true
}

async function submitRegister() {
  if (!pending.value.length) return
  const datasourceId = pending.value[0].datasource_id
  if (pending.value.some((i) => i.datasource_id !== datasourceId)) {
    ElMessage.warning('一次只能登记同一个数据源下的资源')
    return
  }
  registering.value = true
  try {
    const items: RegisterItem[] = pending.value.map((r) =>
      isBatch.value
        ? {
            resource_id: r.id,
            domain_code: regForm.domain_code || null,
            owner_name: regForm.owner_name || null,
          }
        : {
            resource_id: r.id,
            asset_name: regForm.asset_name || null,
            domain_code: regForm.domain_code || null,
            trace_level: regForm.trace_level || null,
            owner_name: regForm.owner_name || null,
          },
    )
    await registerAssets(datasourceId, items)
    ElMessage.success(`已登记 ${pending.value.length} 个资产`)
    registerVisible.value = false
    detailVisible.value = false
    await Promise.all([reload(), loadSummary()])
  } finally {
    registering.value = false
  }
}

async function openDetail(row: ResourceTable) {
  detail.value = await getResource(row.id)
  detailVisible.value = true
}

onMounted(async () => {
  datasources.value = await listDatasources()
  domains.value = await listDomains()
  await Promise.all([reload(), loadSummary()])
})
</script>

<style scoped>
.stat-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.stat {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 14px 16px;
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.stat-label {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.list-card {
  padding: 14px 16px 16px;
}
.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.tname {
  font-weight: 600;
}
.tcomment {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}
.suggest {
  font-size: 12.5px;
}
.suggest-sub {
  margin-left: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}
.dot.ok {
  background: var(--color-success);
  box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.12);
}
.dot.idle {
  background: #c7d3e0;
}
.link {
  cursor: pointer;
}
.link:hover {
  color: var(--color-primary);
}
.ml {
  margin-left: 4px;
}
.pager {
  margin-top: 12px;
  justify-content: flex-end;
}
.d-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 13px;
}
.d-desc {
  margin-bottom: 16px;
}
.d-sub {
  font-size: 13px;
  font-weight: 600;
  margin: 6px 0 10px;
}
.reg-hint {
  font-size: 12.5px;
  color: var(--color-text-secondary);
  margin-bottom: 14px;
}
.batch-form {
  margin-top: 14px;
}
</style>
