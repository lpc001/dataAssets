<template>
  <div v-loading="loading">
    <div class="page-header">
      <div>
        <el-button link type="primary" @click="$router.push('/catalog')">← 返回资产目录</el-button>
        <div class="page-title">{{ asset?.asset_name }}</div>
        <div class="page-sub">
          <span class="mono">{{ asset?.asset_code }}</span>
          <span class="sep">·</span>
          <span class="mono">{{ asset?.schema_name }}.{{ asset?.table_name }}</span>
        </div>
      </div>
      <div class="tags" v-if="asset">
        <el-tag effect="plain">{{ layerLabel(asset.data_layer) }}</el-tag>
        <el-tag type="info">{{ groupLabel(asset) }}</el-tag>
        <el-tag :type="asset.status === 'PUBLISHED' ? 'success' : 'info'">{{ statusLabel(asset.status) }}</el-tag>
      </div>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane label="基本信息" name="base">
        <el-form v-if="asset" :model="form" label-width="110px" class="base-form">
          <el-form-item label="资产名称">
            <el-input v-model="form.asset_name" />
          </el-form-item>
          <el-form-item label="归类">
            <el-select v-model="form.group_type" style="width: 240px">
              <el-option label="业务域" value="DOMAIN" />
              <el-option label="公共维度" value="PUBLIC" />
              <el-option label="跨域专题" value="TOPIC" />
              <el-option label="未归类" value="OTHER" />
            </el-select>
          </el-form-item>
          <el-form-item label="所属数据域">
            <el-select
              v-model="form.domain_code"
              clearable
              style="width: 240px"
              :disabled="form.group_type !== 'DOMAIN'"
              :placeholder="form.group_type === 'DOMAIN' ? '选择业务域' : '非业务域归类无需选择'"
            >
              <el-option v-for="d in domains" :key="d.domain_code" :label="d.domain_name" :value="d.domain_code" />
            </el-select>
          </el-form-item>
          <el-form-item label="追溯档">
            <el-select v-model="form.trace_level" clearable style="width: 160px">
              <el-option label="A 逐条对账" value="A" />
              <el-option label="B 事件流" value="B" />
              <el-option label="C 主数据" value="C" />
              <el-option label="D 汇总" value="D" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status" style="width: 160px">
              <el-option label="已发布" value="PUBLISHED" />
              <el-option label="草稿" value="DRAFT" />
              <el-option label="已下线" value="OFFLINE" />
            </el-select>
          </el-form-item>
          <el-form-item label="责任人">
            <el-input v-model="form.owner_name" style="width: 240px" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="form.description" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
            <el-divider direction="vertical" />
            <el-button v-if="asset.status === 'PUBLISHED'" plain type="warning" @click="toggleStatus('OFFLINE')">
              下架
            </el-button>
            <el-button v-else plain type="success" @click="toggleStatus('PUBLISHED')">重新发布</el-button>
            <span class="action-hint">{{ asset.status === 'PUBLISHED' ? '下架后将从资产目录隐藏，可再发布' : '重新发布后回到资产目录' }}</span>
          </el-form-item>
        </el-form>
        <el-descriptions :column="3" border v-if="asset">
          <el-descriptions-item label="来源表">
            <span class="mono">{{ asset.schema_name }}.{{ asset.table_name }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="数据类型">{{ layerLabel(asset.data_layer) }}</el-descriptions-item>
          <el-descriptions-item label="行数">{{ asset.row_count ?? '—' }}</el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>

      <el-tab-pane :label="`字段清单（${asset?.columns?.length ?? 0}）`" name="columns">
        <el-table :data="asset?.columns ?? []" class="card" size="small">
          <el-table-column prop="ordinal" label="#" width="60" />
          <el-table-column prop="column_name" label="字段" min-width="170">
            <template #default="{ row }"><span class="mono">{{ row.column_name }}</span></template>
          </el-table-column>
          <el-table-column label="业务中文名" min-width="150">
            <template #default="{ row }">{{ row.business_name || row.column_comment || '—' }}</template>
          </el-table-column>
          <el-table-column prop="data_type" label="类型" width="110" />
          <el-table-column label="标记" width="90">
            <template #default="{ row }">
              <el-tag v-if="row.is_key" size="small" type="warning">主键</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="敏感级别" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.sensitive_level === 'L1' ? 'success' : 'danger'">
                {{ row.sensitive_level }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openColumn(row)">标注</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="colVisible" title="字段标注" width="480px">
      <el-form label-width="100px">
        <el-form-item label="字段"><span class="mono">{{ colForm.column_name }}</span></el-form-item>
        <el-form-item label="业务中文名">
          <el-input v-model="colForm.business_name" :placeholder="colForm.column_comment || '选填'" />
        </el-form-item>
        <el-form-item label="业务含义">
          <el-input v-model="colForm.business_meaning" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="敏感级别">
          <el-select v-model="colForm.sensitive_level" style="width: 160px">
            <el-option label="L1 一般" value="L1" />
            <el-option label="L2 敏感" value="L2" />
            <el-option label="L3 最敏感" value="L3" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键字段">
          <el-switch v-model="colForm.is_key" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="colVisible = false">取消</el-button>
        <el-button type="primary" @click="saveColumn">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAsset,
  listDomains,
  patchAsset,
  patchAssetColumn,
  type AssetColumn,
  type AssetDetail,
  type Domain,
} from '@/api/catalog'

const route = useRoute()
const loading = ref(false)
const saving = ref(false)
const tab = ref('base')
const asset = ref<AssetDetail | null>(null)
const domains = ref<Domain[]>([])
const form = reactive<any>({
  asset_name: '',
  group_type: 'DOMAIN',
  domain_code: '',
  trace_level: '',
  status: 'PUBLISHED',
  owner_name: '',
  description: '',
})

const GROUP_LABELS: Record<string, string> = {
  PUBLIC: '公共维度',
  TOPIC: '跨域专题',
  OTHER: '未归类',
}

function groupLabel(row: { group_type: string; domain_code: string | null }) {
  if (row.group_type && row.group_type !== 'DOMAIN') {
    return GROUP_LABELS[row.group_type] || row.group_type
  }
  return `业务域：${row.domain_code || '未选'}`
}
const colVisible = ref(false)
const colForm = reactive<any>({ id: 0, column_name: '', column_comment: '', business_name: '', business_meaning: '', sensitive_level: 'L1', is_key: false })

const LAYER_LABELS: Record<string, string> = {
  DIM: '维度数据',
  DWD: '业务数据',
  DWS: '汇总统计',
  OTHER: '其他',
}
const STATUS_LABELS: Record<string, string> = { PUBLISHED: '已发布', DRAFT: '草稿', OFFLINE: '已下线' }

function layerLabel(layer: string | null | undefined) {
  return layer ? LAYER_LABELS[layer] || layer : '—'
}

function statusLabel(status: string) {
  return STATUS_LABELS[status] || status
}

async function load() {
  loading.value = true
  try {
    const detail = await getAsset(Number(route.params.id))
    asset.value = detail
    Object.assign(form, {
      asset_name: detail.asset_name,
      group_type: detail.group_type || 'DOMAIN',
      domain_code: detail.domain_code || '',
      trace_level: detail.trace_level || '',
      status: detail.status,
      owner_name: detail.owner_name || '',
      description: detail.description || '',
    })
  } finally {
    loading.value = false
  }
}

async function onSave() {
  if (!asset.value) return
  saving.value = true
  try {
    await patchAsset(asset.value.id, {
      asset_name: form.asset_name,
      group_type: form.group_type,
      domain_code: form.group_type === 'DOMAIN' ? form.domain_code || null : null,
      trace_level: form.trace_level || null,
      status: form.status,
      owner_name: form.owner_name || null,
      description: form.description || null,
    })
    ElMessage.success('已保存')
    await load()
  } finally {
    saving.value = false
  }
}

async function toggleStatus(target: 'OFFLINE' | 'PUBLISHED') {
  if (!asset.value) return
  const label = target === 'OFFLINE' ? '下架' : '重新发布'
  await ElMessageBox.confirm(
    target === 'OFFLINE'
      ? `下架后该资产将从资产目录中消失（可按「已下线」筛选找回），确认下架「${asset.value.asset_name}」？`
      : `确认重新发布「${asset.value.asset_name}」？`,
    `${label}确认`,
    { type: 'warning' },
  )
  await patchAsset(asset.value.id, { status: target })
  ElMessage.success(`已${label}`)
  await load()
}

function openColumn(row: AssetColumn) {
  Object.assign(colForm, {
    id: row.id,
    column_name: row.column_name,
    column_comment: row.column_comment || '',
    business_name: row.business_name || row.column_comment || '',
    business_meaning: row.business_meaning || '',
    sensitive_level: row.sensitive_level,
    is_key: row.is_key,
  })
  colVisible.value = true
}

async function saveColumn() {
  await patchAssetColumn(colForm.id, {
    business_name: colForm.business_name || null,
    business_meaning: colForm.business_meaning || null,
    sensitive_level: colForm.sensitive_level,
    is_key: colForm.is_key,
  })
  ElMessage.success('字段标注已保存')
  colVisible.value = false
  await load()
}

onMounted(async () => {
  domains.value = await listDomains()
  await load()
})
</script>

<style scoped>
.head-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.tags {
  display: flex;
  gap: 8px;
}
.base-form {
  max-width: 620px;
  margin-bottom: 18px;
}
.sep {
  margin: 0 6px;
  color: var(--color-border);
}
.action-hint {
  margin-left: 10px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
</style>
