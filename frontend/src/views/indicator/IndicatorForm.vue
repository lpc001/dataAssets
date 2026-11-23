<template>
  <div>
    <div class="page-header">
      <div>
        <el-button link type="primary" @click="$router.push('/indicators')">← 返回指标中心</el-button>
        <div class="page-title">新建指标</div>
        <div class="page-sub">选数据 → 选度量 → 选维度（可关联其他资产）→ 看结果 → 保存</div>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="15">
        <div class="card panel">
          <div class="panel-title"><span class="step">1</span> 选数据</div>
          <el-form label-width="90px">
            <el-form-item label="数据域">
              <el-select v-model="domainCode" style="width: 220px" placeholder="先选数据域" @change="onDomainChange">
                <el-option v-for="d in domains" :key="d.domain_code" :label="d.domain_name" :value="d.domain_code" />
              </el-select>
            </el-form-item>
            <el-form-item label="数据资产">
              <el-select v-model="assetId" style="width: 420px" filterable placeholder="选择已发布的资产" :disabled="!domainCode" @change="onAssetChange">
                <el-option v-for="a in assets" :key="a.id" :label="`${a.asset_name}（${a.table_name}）`" :value="a.id" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <div class="card panel">
          <div class="panel-title"><span class="step">2</span> 统计什么（度量）</div>
          <el-form label-width="90px">
            <el-form-item label="度量字段">
              <el-select v-model="measureId" style="width: 340px" placeholder="选择主资产上的数值字段" :disabled="!assetId">
                <el-option v-for="c in numericColumns" :key="c.id" :label="labelOf(mainAssetName, c)" :value="c.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="聚合方式">
              <el-radio-group v-model="aggregation">
                <el-radio-button label="SUM">求和</el-radio-button>
                <el-radio-button label="AVG">平均</el-radio-button>
                <el-radio-button label="COUNT">计数</el-radio-button>
                <el-radio-button label="MAX">最大</el-radio-button>
                <el-radio-button label="MIN">最小</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-form>
        </div>

        <div class="card panel">
          <div class="panel-title">
            <span class="step">3</span> 关联资产（可选）
            <el-button size="small" text type="primary" :disabled="!assetId" @click="addJoin">+ 添加关联</el-button>
          </div>
          <div v-if="!joins.length" class="join-empty">没有关联资产时，只能使用主资产自己的字段做维度</div>
          <div v-for="(join, index) in joins" :key="index" class="join-row">
            <el-select v-model="join.asset_id" placeholder="关联资产" filterable style="width: 210px" @change="onJoinAssetChange(join)">
              <el-option
                v-for="a in joinableAssets"
                :key="a.id"
                :label="`${a.asset_name}（${a.table_name}）`"
                :value="a.id"
                :disabled="a.id === assetId"
              />
            </el-select>
            <el-select v-model="join.left_column_id" placeholder="主表字段" filterable style="width: 190px">
              <el-option
                v-for="c in mainJoinColumns"
                :key="c.id"
                :label="joinLabel(c, mainAssetName)"
                :value="c.id"
              />
            </el-select>
            <span class="eq">=</span>
            <el-select v-model="join.right_column_id" placeholder="关联表字段" filterable style="width: 190px">
              <el-option
                v-for="c in joinKeyColumns(join.asset_id)"
                :key="c.id"
                :label="joinLabel(c, joinAssetName(join.asset_id))"
                :value="c.id"
              />
            </el-select>
            <el-select v-model="join.join_type" style="width: 90px">
              <el-option label="左连接" value="LEFT" />
              <el-option label="内连接" value="INNER" />
            </el-select>
            <el-button size="small" text type="danger" @click="removeJoin(index)">移除</el-button>
          </div>
        </div>

        <div class="card panel">
          <div class="panel-title"><span class="step">4</span> 按什么分（维度）</div>
          <el-form label-width="90px">
            <el-form-item label="分类维度">
              <el-select v-model="categoryIds" multiple collapse-tags collapse-tags-tooltip style="width: 420px" placeholder="选择字段（可多选）" :disabled="!assetId">
                <el-option v-for="c in categoryColumns" :key="c.id" :label="labelOf(assetNameOf(c), c)" :value="c.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="时间维度">
              <el-select v-model="timeColumnId" clearable style="width: 240px" placeholder="可选" :disabled="!assetId" @change="onTimeChange">
                <el-option v-for="c in timeColumns" :key="c.id" :label="labelOf(assetNameOf(c), c)" :value="c.id" />
              </el-select>
              <el-select v-if="timeColumnId" v-model="timeGrain" style="width: 120px; margin-left: 8px" @change="onGrainChange">
                <el-option label="按年" value="YEAR" />
                <el-option label="按季" value="QUARTER" />
                <el-option label="按月" value="MONTH" />
                <el-option label="按日" value="DAY" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" plain :loading="previewing" @click="onPreview">预览统计结果</el-button>
            </el-form-item>
          </el-form>
        </div>

        <div class="card panel">
          <div class="panel-title"><span class="step">5</span> 保存为指标</div>
          <el-form label-width="90px">
            <el-form-item label="指标名称" required><el-input v-model="name" style="width: 320px" /></el-form-item>
            <el-form-item label="指标编码"><el-input v-model="code" style="width: 220px" placeholder="留空自动生成" /></el-form-item>
            <el-form-item label="指标定义"><el-input v-model="definition" type="textarea" :rows="2" /></el-form-item>
            <el-form-item label="单位">
              <el-select v-model="unit" style="width: 150px">
                <el-option v-for="u in UNITS" :key="u" :label="u" :value="u" />
              </el-select>
            </el-form-item>
            <el-form-item label="周期">
              <el-select v-model="cycle" style="width: 150px" :disabled="hasTimeDimension">
                <el-option label="日" value="日" />
                <el-option label="月" value="月" />
                <el-option label="季" value="季" />
                <el-option label="年" value="年" />
              </el-select>
              <span v-if="hasTimeDimension" class="hint">由时间维度自动确定（{{ cycle }}）</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="onSubmit">保存草稿</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>

      <el-col :span="9">
        <div class="card panel preview-panel">
          <div class="panel-title">结果预览</div>
          <div v-if="!preview" class="preview-empty">选好度量与维度后点「预览统计结果」<br />这里会按维度分组显示真实数据</div>
          <template v-else>
            <div class="hint">{{ preview.hint }}</div>
            <el-table :data="preview.rows" size="small" max-height="420" border>
              <el-table-column v-for="(c, i) in preview.columns" :key="c" :label="c" min-width="110" show-overflow-tooltip>
                <template #default="{ row }">{{ row[i] ?? '—' }}</template>
              </el-table-column>
            </el-table>
          </template>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getAsset, listAssets, listDomains, type Asset, type AssetColumn, type Domain } from '@/api/catalog'
import { createIndicator, previewAggregate, type AggregatePreview } from '@/api/indicator'

const router = useRouter()
const domains = ref<Domain[]>([])
const assets = ref<Asset[]>([])
const allAssets = ref<Asset[]>([])
const columns = ref<AssetColumn[]>([])
const joinColumns = reactive<Record<number, AssetColumn[]>>({})

const domainCode = ref('')
const assetId = ref<number | null>(null)
const measureId = ref<number | null>(null)
const aggregation = ref('SUM')
const categoryIds = ref<number[]>([])
const timeColumnId = ref<number | null>(null)
const timeGrain = ref('MONTH')
const joins = ref<{ asset_id: number | null; left_column_id: number | null; right_column_id: number | null; join_type: string }[]>([])

const name = ref('')
const code = ref('')
const definition = ref('')
const unit = ref('个')
const cycle = ref('月')

const previewing = ref(false)
const saving = ref(false)
const preview = ref<AggregatePreview | null>(null)
const UNITS = ['%', '元', 'm³', '户', '个', '次', '小时', '分钟', '秒', '元/m³']

const GRAIN_CYCLE: Record<string, string> = { YEAR: '年', QUARTER: '季', MONTH: '月', DAY: '日' }
const hasTimeDimension = computed(() => !!timeColumnId.value)
const mainAssetName = computed(() => assets.value.find((a) => a.id === assetId.value)?.asset_name || '')
const joinableAssets = computed(() => allAssets.value.filter((a) => a.id !== assetId.value))

const mainJoinColumns = computed(() => columns.value.filter((c) => !isNumeric(c.data_type)))

function joinKeyColumns(assetId: number | null) {
  if (!assetId) return []
  return (joinColumns[assetId] || []).filter((c) => !isNumeric(c.data_type))
}

function joinAssetName(assetId: number | null) {
  if (!assetId) return ''
  return allAssets.value.find((a) => a.id === assetId)?.asset_name || ''
}

function joinLabel(column: AssetColumn, assetName: string) {
  const cn = column.business_name || column.column_comment || ''
  return `${column.column_name}${cn ? '　' + cn : ''}${assetName ? '（' + assetName + '）' : ''}`
}
const joinedColumns = computed(() => {
  const result: { column: AssetColumn; assetName: string }[] = []
  for (const join of joins.value) {
    if (!join.asset_id) continue
    const assetName = allAssets.value.find((a) => a.id === join.asset_id)?.asset_name || ''
    for (const column of joinColumns[join.asset_id] || []) result.push({ column, assetName })
  }
  return result
})

const isTime = (t: string | null) => /date|time/i.test(t || '')
const isNumeric = (t: string | null) => /int|numeric|decimal|float|double|real|money|number/i.test(t || '')

const numericColumns = computed(() => columns.value.filter((c) => isNumeric(c.data_type)))
const timeOptions = computed(() => [
  ...columns.value.filter((c) => isTime(c.data_type)).map((c) => ({ column: c, assetName: mainAssetName.value })),
  ...joinedColumns.value.filter((x) => isTime(x.column.data_type)),
])
const categoryOptions = computed(() => [
  ...columns.value.filter((c) => !isNumeric(c.data_type) && !isTime(c.data_type)).map((c) => ({ column: c, assetName: mainAssetName.value })),
  ...joinedColumns.value.filter((x) => !isNumeric(x.column.data_type) && !isTime(x.column.data_type)),
])
const timeColumns = computed(() => timeOptions.value.map((x) => x.column))
const categoryColumns = computed(() => categoryOptions.value.map((x) => x.column))

function assetNameOf(column: AssetColumn) {
  if (columns.value.some((c) => c.id === column.id)) return mainAssetName.value
  const hit = joinedColumns.value.find((x) => x.column.id === column.id)
  return hit?.assetName || ''
}

function labelOf(assetName: string, column: AssetColumn) {
  const cn = column.business_name || column.column_comment || ''
  return `${assetName}.${column.column_name}${cn ? '　' + cn : ''}`
}

async function onDomainChange() {
  assetId.value = null
  columns.value = []
  joins.value = []
  preview.value = null
  const res = await listAssets({ domain_code: domainCode.value, status: 'PUBLISHED', page_size: 200 })
  assets.value = res.items
}

async function onAssetChange() {
  measureId.value = null
  categoryIds.value = []
  timeColumnId.value = null
  joins.value = []
  preview.value = null
  if (!assetId.value) return
  const detail = await getAsset(assetId.value)
  columns.value = detail.columns
  if (!name.value) name.value = detail.asset_name
}

function addJoin() {
  joins.value.push({ asset_id: null, left_column_id: null, right_column_id: null, join_type: 'LEFT' })
}

function removeJoin(index: number) {
  joins.value.splice(index, 1)
  categoryIds.value = categoryIds.value.filter((id) => columns.value.some((c) => c.id === id) || joinedColumns.value.some((x) => x.column.id === id))
  if (timeColumnId.value && !timeColumns.value.some((c) => c.id === timeColumnId.value)) timeColumnId.value = null
}

async function onJoinAssetChange(join: any) {
  join.right_column_id = null
  if (join.asset_id && !joinColumns[join.asset_id]) {
    const detail = await getAsset(join.asset_id)
    joinColumns[join.asset_id] = detail.columns
  }
}

function onTimeChange() {
  if (timeColumnId.value) {
    timeGrain.value = 'MONTH'
    cycle.value = GRAIN_CYCLE[timeGrain.value] || '月'
  } else {
    cycle.value = '月'
  }
}

function onGrainChange() {
  if (timeColumnId.value) cycle.value = GRAIN_CYCLE[timeGrain.value] || '月'
}

function buildJoins() {
  return joins.value
    .filter((j) => j.asset_id && j.left_column_id && j.right_column_id)
    .map((j) => ({
      asset_id: j.asset_id as number,
      left_asset_column_id: j.left_column_id as number,
      right_asset_column_id: j.right_column_id as number,
      join_type: j.join_type,
    }))
}

function buildDimensions() {
  const dims: { asset_column_id: number; time_grain?: string }[] = categoryIds.value.map((id) => ({ asset_column_id: id }))
  if (timeColumnId.value) dims.push({ asset_column_id: timeColumnId.value, time_grain: timeGrain.value })
  return dims
}

async function onPreview() {
  if (!assetId.value) {
    ElMessage.warning('请先选择数据资产')
    return
  }
  previewing.value = true
  try {
    preview.value = await previewAggregate({
      asset_id: assetId.value,
      measure_asset_column_id: measureId.value,
      aggregation: aggregation.value,
      dimensions: buildDimensions(),
      joins: buildJoins(),
    })
  } finally {
    previewing.value = false
  }
}

async function onSubmit() {
  if (!assetId.value || !name.value || !measureId.value) {
    ElMessage.warning('请选择资产、度量字段并填写指标名称')
    return
  }
  saving.value = true
  try {
    const created = await createIndicator({
      indicator_name: name.value,
      indicator_code: code.value || null,
      indicator_def: definition.value || null,
      source_asset_column_id: measureId.value,
      aggregation: aggregation.value,
      dimensions: buildDimensions(),
      joins: buildJoins(),
      unit: unit.value,
      cycle: cycle.value,
    })
    ElMessage.success(`已创建草稿 ${created.indicator_code}`)
    router.replace(`/indicators/${created.id}`)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  domains.value = await listDomains()
  const all = await listAssets({ status: 'PUBLISHED', page_size: 200 })
  allAssets.value = all.items
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
  display: flex;
  align-items: center;
  gap: 8px;
}
.step {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-tint);
  color: var(--color-primary);
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.hint {
  margin-left: 10px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.join-empty {
  font-size: 12px;
  color: var(--color-text-secondary);
}
.join-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.eq {
  color: var(--color-text-secondary);
}
.preview-panel {
  min-height: 320px;
}
.preview-empty {
  padding: 60px 10px;
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.8;
}
</style>
