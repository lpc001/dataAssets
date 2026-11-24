<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">数据源管理</div>
        <div class="page-sub">配置目标库只读连接，采集元数据到资源池，并保留每次采集的版本与变化</div>
      </div>
      <div class="page-actions">
        <el-button :loading="loading" @click="reload">刷新</el-button>
        <el-button type="primary" @click="openCreate">新增数据源</el-button>
      </div>
    </div>

    <div class="stat-row">
      <div class="stat"><div class="stat-value">{{ summary.resource_count }}</div><div class="stat-label">资源表</div></div>
      <div class="stat"><div class="stat-value">{{ summary.asset_count }}</div><div class="stat-label">已登记资产</div></div>
      <div class="stat"><div class="stat-value">{{ summary.column_count }}</div><div class="stat-label">资源字段</div></div>
      <div class="stat stat-wide"><div class="stat-value sm">{{ lastSyncText }}</div><div class="stat-label">最近采集</div></div>
    </div>

    <div class="card list-card">
      <div class="list-head">
        <span class="list-title">已配置数据源</span>
        <span class="list-hint">采集只更新资源池，不会改动已登记资产的业务标注</span>
      </div>

      <el-table v-if="list.length" :data="list" v-loading="loading" class="ds-table">
        <el-table-column label="数据源" min-width="220">
          <template #default="{ row }">
            <div class="ds-name">
              {{ row.name }}
              <el-tag size="small" effect="plain" class="engine">PostgreSQL</el-tag>
            </div>
            <div class="ds-conn mono">{{ row.host }}:{{ row.port }}/{{ row.database_name }}</div>
          </template>
        </el-table-column>

        <el-table-column label="采集 Schema" min-width="170">
          <template #default="{ row }">
            <el-tag v-for="s in splitSchemas(row.schema_filter)" :key="s" size="small" class="schema-chip">{{ s }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="连接状态" width="130">
          <template #default="{ row }">
            <span class="status">
              <i class="dot" :class="row.readonly_verified ? 'ok' : 'warn'" />
              {{ row.readonly_verified ? '只读账号' : '非只读' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="最后采集" width="170">
          <template #default="{ row }"><span class="time">{{ fmt(row.last_sync_at) }}</span></template>
        </el-table-column>

        <el-table-column label="操作" width="330" align="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="onSync(row)">采集</el-button>
            <el-button size="small" text @click="onTest(row)">测试</el-button>
            <el-button size="small" text @click="openVersions(row)">版本</el-button>
            <el-button size="small" text @click="openEdit(row)">编辑</el-button>
            <el-button size="small" text type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-else class="empty">
        <div class="empty-drop"></div>
        <div class="empty-title">还没有配置数据源</div>
        <div class="empty-sub">添加一个只读连接，即可把目标库的表与字段采集进资源池</div>
        <el-button type="primary" @click="openCreate">新增数据源</el-button>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑数据源' : '新增数据源'" width="560px">
      <div class="form-section">连接信息</div>
      <el-form :model="form" label-width="92px" label-position="left">
        <el-form-item label="名称" required><el-input v-model="form.name" placeholder="如 water_dw 生产模型库" /></el-form-item>
        <el-form-item label="主机" required><el-input v-model="form.host" placeholder="localhost" /></el-form-item>
        <el-form-item label="端口">
          <el-input-number v-model="form.port" :min="1" :max="65535" controls-position="right" />
        </el-form-item>
        <el-form-item label="数据库" required><el-input v-model="form.database_name" placeholder="water_dw" /></el-form-item>
        <el-form-item label="Schema">
          <div class="schema-row">
            <el-select
              v-model="schemaList"
              multiple
              filterable
              allow-create
              default-first-option
              style="flex: 1"
              placeholder="可多选，也可直接输入"
            >
              <el-option v-for="s in schemaOptions" :key="s" :label="s" :value="s" />
            </el-select>
            <el-button :loading="schemaLoading" @click="loadSchemas()">加载</el-button>
          </div>
        </el-form-item>
      </el-form>
      <div class="form-section">账号与备注</div>
      <el-form :model="form" label-width="92px" label-position="left">
        <el-form-item label="只读账号" required><el-input v-model="form.username" placeholder="reader" /></el-form-item>
        <el-form-item label="口令">
          <el-input v-model="form.password" type="password" show-password :placeholder="form.id ? '留空表示不修改' : '只读账号口令'" />
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" placeholder="选填" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="versionsVisible" title="采集版本" size="720px">
      <div class="drawer-hint">每次采集生成一个版本，记录表/字段的新增、变更与消失</div>
      <el-table :data="versions" size="small" v-loading="versionsLoading">
        <el-table-column label="版本" width="70">
          <template #default="{ row }"><span class="mono">v{{ row.version_no }}</span></template>
        </el-table-column>
        <el-table-column label="时间" width="150">
          <template #default="{ row }"><span class="time">{{ fmt(row.started_at) }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <span class="status">
              <i class="dot" :class="row.status === 'SUCCESS' ? 'ok' : 'bad'" />
              {{ row.status === 'SUCCESS' ? '成功' : '失败' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="表 增/变/删" width="100">
          <template #default="{ row }">{{ row.table_added }}/{{ row.table_changed }}/{{ row.table_dropped }}</template>
        </el-table-column>
        <el-table-column label="字段 增/变/删" width="110">
          <template #default="{ row }">{{ row.column_added }}/{{ row.column_changed }}/{{ row.column_dropped }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openChanges(row)">查看变化</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!versionsLoading && !versions.length" description="还没有采集记录" :image-size="80" />
    </el-drawer>

    <el-dialog v-model="changesVisible" :title="`版本 v${currentVersion?.version_no ?? ''} 的变化`" width="860px">
      <el-table :data="changes" size="small" max-height="480">
        <el-table-column label="对象" width="80">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.object_type === 'TABLE' ? '表' : '字段' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="位置" min-width="220">
          <template #default="{ row }">
            <span class="mono">{{ row.table_name }}</span>
            <span v-if="row.column_name" class="mono col">.{{ row.column_name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="变化" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.change_type === 'ADD' ? 'success' : row.change_type === 'DROP' ? 'danger' : 'warning'">
              {{ changeLabel(row.change_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="field_name" label="属性" width="110" />
        <el-table-column label="变化前" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.old_value ?? '—' }}</template>
        </el-table-column>
        <el-table-column label="变化后" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.new_value ?? '—' }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!changes.length" description="本次采集没有结构变化" :image-size="70" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { assetSummary } from '@/api/catalog'
import {
  createDatasource,
  deleteDatasource,
  fetchSchemas,
  listDatasources,
  listVersionChanges,
  listVersions,
  syncDatasource,
  testDatasource,
  updateDatasource,
  type DataSource,
  type MetaChange,
  type MetaVersion,
} from '@/api/datasource'

const list = ref<DataSource[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const versionsVisible = ref(false)
const versionsLoading = ref(false)
const versions = ref<MetaVersion[]>([])
const changesVisible = ref(false)
const changes = ref<MetaChange[]>([])
const schemaOptions = ref<string[]>([])
const schemaList = ref<string[]>([])
const schemaLoading = ref(false)
const currentVersion = ref<MetaVersion | null>(null)
const summary = reactive({ datasource_count: 0, resource_count: 0, asset_count: 0, column_count: 0, domain_count: 0, missing_count: 0 })

const form = reactive<any>({
  id: null,
  name: '',
  host: 'localhost',
  port: 5432,
  database_name: '',
  schema_filter: 'public',
  username: 'reader',
  password: '',
  remark: '',
})

const lastSyncText = computed(() => {
  const times = list.value.map((x) => x.last_sync_at).filter(Boolean) as string[]
  if (!times.length) return '尚未采集'
  return times.sort().slice(-1)[0].replace('T', ' ').slice(0, 16)
})

function splitSchemas(value: string) {
  return (value || '').split(',').map((s) => s.trim()).filter(Boolean)
}

const CHANGE_LABELS: Record<string, string> = { ADD: '新增', MODIFY: '变更', DROP: '消失' }

function changeLabel(type: string) {
  return CHANGE_LABELS[type] || type
}

function fmt(value: string | null) {
  return value ? value.replace('T', ' ').slice(0, 19) : '—'
}

async function load() {
  loading.value = true
  try {
    list.value = await listDatasources()
  } finally {
    loading.value = false
  }
}

async function reload() {
  await load()
  Object.assign(summary, await assetSummary())
}

function openCreate() {
  Object.assign(form, {
    id: null, name: '', host: 'localhost', port: 5432, database_name: '',
    schema_filter: 'public', username: 'reader', password: '', remark: '',
  })
  schemaList.value = []
  schemaOptions.value = []
  dialogVisible.value = true
}

async function openEdit(row: DataSource) {
  Object.assign(form, { ...row, password: '' })
  schemaList.value = (row.schema_filter || '').split(',').map((s) => s.trim()).filter(Boolean)
  schemaOptions.value = [...schemaList.value]
  dialogVisible.value = true
  await loadSchemas(row.id)
}

async function loadSchemas(datasourceId?: number) {
  if (!form.host || !form.database_name || !form.username) {
    ElMessage.warning('请先填写主机、数据库与账号')
    return
  }
  if (!form.password && !(datasourceId || form.id)) {
    ElMessage.warning('请先填写口令')
    return
  }
  schemaLoading.value = true
  try {
    const res = await fetchSchemas({
      host: form.host,
      port: form.port,
      database_name: form.database_name,
      username: form.username,
      password: form.password || undefined,
      datasource_id: datasourceId || form.id || undefined,
    })
    schemaOptions.value = res.schemas
    ElMessage.success(`已加载 ${res.schemas.length} 个 Schema`)
  } finally {
    schemaLoading.value = false
  }
}

async function onSave() {
  if (!form.name || !form.host || !form.database_name || !form.username) {
    ElMessage.warning('请填写名称、主机、数据库与账号')
    return
  }
  saving.value = true
  form.schema_filter = schemaList.value.join(',') || 'public'
  try {
    if (form.id) {
      const payload: any = {
        name: form.name, host: form.host, port: form.port, database_name: form.database_name,
        schema_filter: form.schema_filter, username: form.username, remark: form.remark,
      }
      if (form.password) payload.password = form.password
      await updateDatasource(form.id, payload)
      ElMessage.success('已保存')
    } else {
      if (!form.password) {
        ElMessage.warning('请填写口令')
        return
      }
      await createDatasource({ ...form })
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await reload()
  } finally {
    saving.value = false
  }
}

async function onTest(row: DataSource) {
  const res = await testDatasource(row.id)
  if (res.ok) {
    ElMessage.success(res.readonly ? '连接成功，账号为只读' : '连接成功，但账号不是只读账号')
  } else {
    ElMessage.error(res.message)
  }
  await load()
}

async function onSync(row: DataSource) {
  await ElMessageBox.confirm(`确认从「${row.name}」采集元数据？`, '采集确认', { type: 'info' })
  const version = await syncDatasource(row.id)
  ElMessage.success(
    `采集完成 v${version.version_no}：表新增 ${version.table_added}、变更 ${version.table_changed}、消失 ${version.table_dropped}；字段新增 ${version.column_added}`,
  )
  await reload()
}

async function openVersions(row: DataSource) {
  versionsVisible.value = true
  versionsLoading.value = true
  try {
    versions.value = await listVersions(row.id)
  } finally {
    versionsLoading.value = false
  }
}

async function openChanges(version: MetaVersion) {
  currentVersion.value = version
  changes.value = await listVersionChanges(version.id)
  changesVisible.value = true
}

async function onDelete(row: DataSource) {
  await ElMessageBox.confirm(
    `删除数据源「${row.name}」将同时删除其资源、已登记资产与采集版本，确认？`,
    '删除确认',
    { type: 'warning' },
  )
  await deleteDatasource(row.id)
  ElMessage.success('已删除')
  await reload()
}

onMounted(reload)
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
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}
.stat-value.sm {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-secondary);
  padding-top: 5px;
}
.stat-label {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.list-card {
  padding: 4px 4px 10px;
  overflow: hidden;
}
.list-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px 10px;
}
.list-title {
  font-size: 14px;
  font-weight: 600;
}
.list-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
}
.ds-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 13.5px;
}
.engine {
  font-weight: 400;
  color: var(--color-text-secondary);
}
.ds-conn {
  margin-top: 3px;
  color: var(--color-text-secondary);
}
.schema-chip {
  margin-right: 6px;
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
  display: inline-block;
}
.dot.ok {
  background: var(--color-success);
  box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.12);
}
.dot.warn {
  background: var(--color-warning);
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.14);
}
.dot.bad {
  background: var(--color-danger);
  box-shadow: 0 0 0 3px rgba(226, 61, 109, 0.12);
}
.time {
  color: var(--color-text-secondary);
  font-size: 12.5px;
}
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 54px 0 60px;
}
.empty-drop {
  width: 34px;
  height: 34px;
  border-radius: 50% 50% 50% 0;
  transform: rotate(-45deg);
  background: var(--gradient-primary);
  opacity: 0.85;
}
.empty-title {
  margin-top: 6px;
  font-size: 14px;
  font-weight: 600;
}
.empty-sub {
  font-size: 12.5px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}
.form-section {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  letter-spacing: 0.04em;
  margin: 4px 0 12px;
  padding-left: 2px;
}
.form-section:not(:first-child) {
  margin-top: 18px;
}
.drawer-hint {
  font-size: 12.5px;
  color: var(--color-text-secondary);
  margin-bottom: 10px;
}
.col {
  color: var(--color-text-secondary);
}
</style>
