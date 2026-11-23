<template>
  <div v-loading="loading">
    <div class="page-header">
      <div>
        <el-button link type="primary" @click="$router.push('/indicators')">← 返回指标中心</el-button>
        <div class="page-title">{{ data?.indicator_name }}</div>
        <div class="page-sub mono">{{ data?.indicator_code }}</div>
      </div>
      <div class="page-actions">
        <el-tag :type="statusType(data?.status)">{{ statusLabel(data?.status) }}</el-tag>
        <el-button v-if="data?.status === 'DRAFT'" type="primary" :loading="saving" @click="onPublish">发布</el-button>
        <el-button v-if="data?.status === 'PUBLISHED'" plain type="warning" @click="onRetire">废止</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="14">
        <div class="card panel">
          <div class="panel-title">指标信息</div>
          <el-form :model="form" label-width="100px">
            <el-form-item label="名称"><el-input v-model="form.indicator_name" /></el-form-item>
            <el-form-item label="定义"><el-input v-model="form.indicator_def" type="textarea" :rows="2" /></el-form-item>
            <el-form-item label="公式"><el-input v-model="form.formula" /></el-form-item>
            <el-form-item label="单位">
              <el-select v-model="form.unit" style="width: 160px">
                <el-option v-for="u in UNITS" :key="u" :label="u" :value="u" />
              </el-select>
            </el-form-item>
            <el-form-item label="周期">
              <el-select v-model="form.cycle" style="width: 160px">
                <el-option label="日" value="日" />
                <el-option label="月" value="月" />
                <el-option label="年" value="年" />
              </el-select>
            </el-form-item>
            <el-form-item label="责任人"><el-input v-model="form.owner_name" style="width: 240px" /></el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
              <span class="hint">修改已发布指标会退回草稿</span>
            </el-form-item>
          </el-form>
        </div>

        <div class="card panel">
          <div class="panel-title">取数路径</div>
          <div v-if="data?.source_path" class="path">
            <div class="path-row"><span class="label">数据域</span>{{ domainName(data.domain_code) }}</div>
            <div class="path-row"><span class="label">来源资产</span>{{ data.source_path.asset_name }}</div>
            <div class="path-row">
              <span class="label">取数字段</span>
              <span class="mono">{{ data.source_path.schema_name }}.{{ data.source_path.table_name }}.{{ data.source_path.column_name }}</span>
              <span class="type">{{ data.source_path.data_type }}</span>
            </div>
            <div class="path-row"><span class="label">数据来源</span>由该资产所属数据源提供（只读）</div>
          </div>
          <el-alert v-else type="error" :closable="false" show-icon title="来源字段未挂载，无法发布" />
        </div>
      </el-col>

      <el-col :span="10">
        <div class="card panel">
          <div class="panel-title">校验结果</div>
          <el-table :data="data?.issues ?? []" size="small" max-height="300">
            <el-table-column label="级别" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.severity === 'BLOCK' ? 'danger' : 'warning'">
                  {{ row.severity === 'BLOCK' ? '阻断' : '警告' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="rule_name" label="规则" width="110" />
            <el-table-column prop="message" label="说明" min-width="170" show-overflow-tooltip />
          </el-table>
          <el-empty v-if="data && !data.issues.length" description="校验通过" :image-size="60" />
        </div>

        <div class="card panel">
          <div class="panel-title">版本历史</div>
          <div v-for="v in data?.versions ?? []" :key="v.version_no" class="version">
            v{{ v.version_no }} · {{ v.comment }} · {{ v.changed_by }} · {{ fmt(v.changed_at) }}
          </div>
          <div v-if="!data?.versions?.length" class="empty">暂无变更</div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listDomains, type Domain } from '@/api/catalog'
import { getIndicator, publishIndicator, retireIndicator, updateIndicator, type IndicatorDetail } from '@/api/indicator'

const route = useRoute()
const loading = ref(false)
const saving = ref(false)
const data = ref<IndicatorDetail | null>(null)
const domains = ref<Domain[]>([])
const UNITS = ['%', '元', 'm³', '户', '个', '次', '小时', '分钟', '秒', '元/m³']
const form = reactive<any>({ indicator_name: '', indicator_def: '', formula: '', unit: '', cycle: '', owner_name: '' })

const STATUS_LABELS: Record<string, string> = { DRAFT: '草稿', PUBLISHED: '已发布', RETIRED: '已废止' }

function statusLabel(status?: string) {
  return status ? STATUS_LABELS[status] || status : ''
}

function statusType(status?: string) {
  return status === 'PUBLISHED' ? 'success' : status === 'RETIRED' ? 'info' : 'warning'
}

function domainName(code: string | null) {
  if (!code) return '公共'
  return domains.value.find((d) => d.domain_code === code)?.domain_name || code
}

function fmt(value: string | null) {
  return value ? value.replace('T', ' ').slice(0, 16) : '—'
}

async function load() {
  loading.value = true
  try {
    const detail = await getIndicator(Number(route.params.id))
    data.value = detail
    Object.assign(form, {
      indicator_name: detail.indicator_name,
      indicator_def: detail.indicator_def || '',
      formula: detail.formula || '',
      unit: detail.unit || '',
      cycle: detail.cycle || '',
      owner_name: detail.owner_name || '',
    })
  } finally {
    loading.value = false
  }
}

async function onSave() {
  saving.value = true
  try {
    await updateIndicator(Number(route.params.id), { ...form })
    ElMessage.success('已保存')
    await load()
  } finally {
    saving.value = false
  }
}

async function onPublish() {
  try {
    await publishIndicator(Number(route.params.id))
    ElMessage.success('已发布')
    await load()
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    if (detail?.issues) {
      ElMessage.error(`存在 ${detail.issues.filter((i: any) => i.severity === 'BLOCK').length} 个阻断问题，不能发布`)
    } else {
      ElMessage.error(typeof detail === 'string' ? detail : '发布失败')
    }
  }
}

async function onRetire() {
  await ElMessageBox.confirm('废止后指标保留历史但不可再引用，确认？', '废止确认', { type: 'warning' })
  await retireIndicator(Number(route.params.id))
  ElMessage.success('已废止')
  await load()
}

onMounted(async () => {
  domains.value = await listDomains()
  await load()
})
</script>

<style scoped>
.panel {
  padding: 16px 18px;
  margin-bottom: 16px;
}
.panel-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}
.path-row {
  font-size: 13px;
  margin-bottom: 8px;
}
.label {
  display: inline-block;
  width: 84px;
  color: var(--color-text-secondary);
}
.type {
  margin-left: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.version {
  font-size: 12.5px;
  color: var(--color-text-secondary);
  padding: 6px 0;
  border-bottom: 1px dashed var(--color-border);
}
.empty {
  font-size: 12.5px;
  color: var(--color-text-secondary);
}
.hint {
  margin-left: 12px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
</style>
