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
      <div class="quick-row">
        <span class="quick-label">快速定位</span>
        <span
          v-for="q in QUICK_FILTERS"
          :key="q.key"
          class="chip"
          :class="{ active: quickFilter === q.key }"
          @click="applyQuick(q.key)"
        >
          {{ q.label }}
        </span>
      </div>

      <div class="filters">
        <el-select v-model="filters.datasource_id" placeholder="全部数据源" clearable style="width: 200px" @change="reload">
          <el-option v-for="d in datasources" :key="d.id" :label="d.name" :value="d.id" />
        </el-select>
        <el-select v-model="filters.kind" placeholder="全部对象" clearable style="width: 120px" @change="reload">
          <el-option label="表" value="TABLE" />
          <el-option label="视图" value="VIEW" />
        </el-select>
        <el-select v-model="filters.flag" placeholder="全部标记" clearable style="width: 130px" @change="reload">
          <el-option label="系统表" value="SYSTEM" />
          <el-option label="临时/备份" value="TEMP" />
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
        <el-table-column label="建议归属" width="150">
          <template #default="{ row }">
            <span class="suggest">{{ suggestGroupLabel(row) }}</span>
            <span class="suggest-sub">{{ suggestGroup(row) === 'DOMAIN' ? domainLabel(row.suggested_domain) : '' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="row_count" label="行数" width="90" align="right" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <span class="status">
              <i class="dot" :class="statusDot(row)" />
              {{ statusText(row) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="190" align="right">
          <template #default="{ row }">
            <el-button v-if="!row.registered" size="small" type="primary" @click="openRegister([row])">登记</el-button>
            <el-button
              v-else-if="row.asset_status === 'OFFLINE'"
              size="small"
              type="success"
              @click="onRepublish(row)"
            >
              重新发布
            </el-button>
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

        <div class="d-flags">
          <span class="d-flags-label">标记</span>
          <el-check-tag :checked="detail.is_system" @change="toggleFlag('is_system', $event)">系统表</el-check-tag>
          <el-check-tag :checked="detail.is_temp" @change="toggleFlag('is_temp', $event)">临时/备份</el-check-tag>
          <span class="d-flags-hint">由表名/所属 schema 规则自动识别，可手动修正</span>
        </div>

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
        <el-button
          v-if="detail && detail.asset_status === 'OFFLINE'"
          type="success"
          @click="onRepublish(detail)"
        >
          重新发布
        </el-button>
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
        <el-form-item label="归类">
          <el-select v-model="regForm.group_type" style="width: 240px">
            <el-option label="业务域" value="DOMAIN" />
            <el-option label="公共维度" value="PUBLIC" />
            <el-option label="跨域专题" value="TOPIC" />
            <el-option label="未归类" value="OTHER" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属数据域">
          <el-select
            v-model="regForm.domain_code"
            clearable
            style="width: 240px"
            :disabled="regForm.group_type !== 'DOMAIN'"
            :placeholder="regForm.group_type === 'DOMAIN' ? '选择业务域' : '非业务域归类无需选择'"
          >
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
          <el-form-item label="统一归类">
            <el-select v-model="regForm.group_type" clearable style="width: 240px" placeholder="不选则按各自建议">
              <el-option label="业务域" value="DOMAIN" />
              <el-option label="公共维度" value="PUBLIC" />
              <el-option label="跨域专题" value="TOPIC" />
              <el-option label="未归类" value="OTHER" />
            </el-select>
          </el-form-item>
          <el-form-item label="统一归属域">
            <el-select
              v-model="regForm.domain_code"
              clearable
              style="width: 240px"
              :disabled="!!regForm.group_type && regForm.group_type !== 'DOMAIN'"
              placeholder="不选则按各自建议"
            >
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
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  assetSummary,
  getResource,
  listDomains,
  listResources,
  patchAsset,
  patchResource,
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
  group_type: 'DOMAIN',
  domain_code: '' as string | null,
  trace_level: '' as string | null,
  owner_name: '',
})

const GROUP_LABELS: Record<string, string> = {
  PUBLIC: '公共维度',
  TOPIC: '跨域专题',
  OTHER: '未归类',
}

function suggestGroup(row: ResourceTable) {
  if (row.suggested_layer === 'DIM') return 'PUBLIC'
  if (row.suggested_layer === 'DWS' && !row.suggested_domain) return 'TOPIC'
  if (!row.suggested_domain) return 'OTHER'
  return 'DOMAIN'
}

function suggestGroupLabel(row: ResourceTable) {
  const group = suggestGroup(row)
  return group === 'DOMAIN' ? layerLabel(row.suggested_layer) : GROUP_LABELS[group] || group
}

function statusText(row: ResourceTable) {
  if (!row.registered) return '待登记'
  if (row.asset_status === 'OFFLINE') return '已下线'
  if (row.asset_status === 'DRAFT') return '草稿'
  return '已发布'
}

function statusDot(row: ResourceTable) {
  if (!row.registered) return 'idle'
  if (row.asset_status === 'OFFLINE') return 'warn'
  return 'ok'
}

const filters = reactive({
  datasource_id: null as number | null,
  kind: '',
  flag: '',
  keyword: '',
  page: 1,
  page_size: 20,
})

const quickFilter = ref('')

const QUICK_FILTERS = [
  { key: '', label: '全部' },
  { key: 'UNREGISTERED', label: '待登记' },
  { key: 'PUBLISHED', label: '已发布' },
  { key: 'OFFLINE', label: '已下线' },
  { key: 'OTHER', label: '未归类' },
]

function applyQuick(key: string) {
  quickFilter.value = key
  filters.page = 1
  reload()
}

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
    if (filters.kind) params.kind = filters.kind
    const quick = quickFilter.value
    if (quick === 'UNREGISTERED') params.asset_status = 'UNREGISTERED'
    else if (quick === 'PUBLISHED' || quick === 'OFFLINE') params.asset_status = quick
    else if (quick === 'OTHER') params.group_type = quick
    if (filters.flag === 'SYSTEM') params.is_system = true
    if (filters.flag === 'TEMP') params.is_temp = true
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
    group_type: isBatch.value ? '' : suggestGroup(targets[0]),
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
    const items: RegisterItem[] = pending.value.map((r) => {
      const group = (isBatch.value ? regForm.group_type : regForm.group_type) || null
      const domain = !group || group === 'DOMAIN' ? regForm.domain_code || null : null
      return isBatch.value
        ? {
            resource_id: r.id,
            group_type: group,
            domain_code: domain,
            owner_name: regForm.owner_name || null,
          }
        : {
            resource_id: r.id,
            asset_name: regForm.asset_name || null,
            group_type: group,
            domain_code: domain,
            trace_level: regForm.trace_level || null,
            owner_name: regForm.owner_name || null,
          }
    })
    await registerAssets(datasourceId, items)
    ElMessage.success(`已登记 ${pending.value.length} 个资产`)
    registerVisible.value = false
    detailVisible.value = false
    await Promise.all([reload(), loadSummary()])
  } finally {
    registering.value = false
  }
}

async function onRepublish(row: ResourceTable) {
  const id = row.asset_id
  if (!id) return
  await ElMessageBox.confirm(`确认重新发布「${row.table_comment || row.table_name}」？`, '重新发布确认', {
    type: 'info',
    confirmButtonText: '确认发布',
    cancelButtonText: '取消',
  })
  await patchAsset(id, { status: 'PUBLISHED' })
  ElMessage.success('已重新发布')
  detailVisible.value = false
  await Promise.all([reload(), loadSummary()])
}

async function openDetail(row: ResourceTable) {
  detail.value = await getResource(row.id)
  detailVisible.value = true
}

async function toggleFlag(field: 'is_system' | 'is_temp', value: boolean) {
  if (!detail.value) return
  await patchResource(detail.value.id, { [field]: value })
  detail.value = await getResource(detail.value.id)
  await Promise.all([reload(), loadSummary()])
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
.quick-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.quick-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-right: 2px;
}
.chip {
  padding: 4px 12px;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  font-size: 12.5px;
  cursor: pointer;
  user-select: none;
  transition: all 0.15s ease;
}
.chip:hover {
  border-color: var(--color-primary-light);
  color: var(--color-primary);
}
.chip.active {
  background: var(--color-tint);
  border-color: var(--color-primary);
  color: var(--color-primary);
  font-weight: 600;
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
.d-flags {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}
.d-flags-label {
  font-size: 12.5px;
  color: var(--color-text-secondary);
}
.d-flags-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
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
