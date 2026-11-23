<template>
  <div>
    <div class="page-header">
      <div>
        <el-button link type="primary" @click="$router.push('/indicators')">← 返回指标中心</el-button>
        <div class="page-title">新建指标</div>
        <div class="page-sub">选数据 → 选度量 → 选维度 → 看结果 → 保存，不需要写 SQL</div>
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
              <el-select v-model="assetId" style="width: 380px" filterable placeholder="选择已发布的资产" :disabled="!domainCode" @change="onAssetChange">
                <el-option v-for="a in assets" :key="a.id" :label="`${a.asset_name}（${a.table_name}）`" :value="a.id" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <div class="card panel">
          <div class="panel-title"><span class="step">2</span> 统计什么（度量）</div>
          <el-form label-width="90px">
            <el-form-item label="度量字段">
              <el-select v-model="measureId" style="width: 320px" placeholder="选择数值字段" :disabled="!assetId">
                <el-option v-for="c in numericColumns" :key="c.id" :label="`${c.column_name}　${c.business_name || c.column_comment || ''}`" :value="c.id" />
              </el-select>
              <span class="hint">聚合选"计数"时统计该字段的非空记录数</span>
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
          <div class="panel-title"><span class="step">3</span> 按什么分（维度）</div>
          <el-form label-width="90px">
            <el-form-item label="分类维度">
              <el-select v-model="categoryIds" multiple collapse-tags collapse-tags-tooltip style="width: 420px" placeholder="选择分类字段（可多选）" :disabled="!assetId">
                <el-option v-for="c in categoryColumns" :key="c.id" :label="`${c.column_name}　${c.business_name || c.column_comment || ''}`" :value="c.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="时间维度">
              <el-select v-model="timeColumnId" clearable style="width: 240px" placeholder="可选" :disabled="!assetId" @change="onTimeChange">
                <el-option v-for="c in timeColumns" :key="c.id" :label="c.column_name" :value="c.id" />
              </el-select>
              <el-select v-if="timeColumnId" v-model="timeGrain" style="width: 130px; margin-left: 8px">
                <el-option label="按年" value="YEAR" />
                <el-option label="按季" value="QUARTER" />
                <el-option label="按月" value="MONTH" />
                <el-option label="按日" value="DAY" />
              </el-select>
              <span class="hint">如 bill_date（YYYY-MM-DD）可统计到月</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" plain :loading="previewing" @click="onPreview">预览统计结果</el-button>
            </el-form-item>
          </el-form>
        </div>

        <div class="card panel">
          <div class="panel-title"><span class="step">4</span> 保存为指标</div>
          <el-form label-width="90px">
            <el-form-item label="指标名称" required><el-input v-model="name" style="width: 320px" placeholder="如 售水量" /></el-form-item>
            <el-form-item label="指标编码"><el-input v-model="code" style="width: 220px" placeholder="留空自动生成" /></el-form-item>
            <el-form-item label="指标定义"><el-input v-model="definition" type="textarea" :rows="2" placeholder="一句话说明这个指标算什么" /></el-form-item>
            <el-form-item label="单位">
              <el-select v-model="unit" style="width: 150px">
                <el-option v-for="u in UNITS" :key="u" :label="u" :value="u" />
              </el-select>
            </el-form-item>
            <el-form-item label="周期">
              <el-select v-model="cycle" style="width: 150px">
                <el-option label="日" value="日" />
                <el-option label="月" value="月" />
                <el-option label="年" value="年" />
              </el-select>
            </el-form-item>
            <el-form-item label="关联口径">
              <el-select v-model="caliberId" clearable style="width: 360px" placeholder="可选">
                <el-option v-for="c in calibers" :key="c.id" :label="`${c.caliber_code} ${c.caliber_name}`" :value="c.id" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="onSubmit">保存草稿</el-button>
              <span class="hint">保存后可去详情页校验并发布</span>
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
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getAsset, listAssets, listDomains, type Asset, type AssetColumn, type Domain } from '@/api/catalog'
import { createIndicator, listCalibers, previewAggregate, type AggregatePreview, type Caliber } from '@/api/indicator'

const router = useRouter()
const domains = ref<Domain[]>([])
const assets = ref<Asset[]>([])
const columns = ref<AssetColumn[]>([])
const calibers = ref<Caliber[]>([])

const domainCode = ref('')
const assetId = ref<number | null>(null)
const measureId = ref<number | null>(null)
const aggregation = ref('SUM')
const categoryIds = ref<number[]>([])
const timeColumnId = ref<number | null>(null)
const timeGrain = ref('MONTH')

const name = ref('')
const code = ref('')
const definition = ref('')
const unit = ref('个')
const cycle = ref('月')
const caliberId = ref<number | null>(null)

const previewing = ref(false)
const saving = ref(false)
const preview = ref<AggregatePreview | null>(null)
const UNITS = ['%', '元', 'm³', '户', '个', '次', '小时', '分钟', '秒', '元/m³']

const isTime = (t: string | null) => /date|time/i.test(t || '')
const isNumeric = (t: string | null) => /int|numeric|decimal|float|double|real|money|number/i.test(t || '')

const numericColumns = computed(() => columns.value.filter((c) => isNumeric(c.data_type)))
const timeColumns = computed(() => columns.value.filter((c) => isTime(c.data_type)))
const categoryColumns = computed(() =>
  columns.value.filter((c) => !isNumeric(c.data_type) && !isTime(c.data_type)),
)

async function onDomainChange() {
  assetId.value = null
  columns.value = []
  preview.value = null
  const res = await listAssets({ domain_code: domainCode.value, status: 'PUBLISHED', page_size: 200 })
  assets.value = res.items
}

async function onAssetChange() {
  measureId.value = null
  categoryIds.value = []
  timeColumnId.value = null
  preview.value = null
  if (!assetId.value) return
  const detail = await getAsset(assetId.value)
  columns.value = detail.columns
  if (!name.value) name.value = detail.asset_name
}

function onTimeChange() {
  if (timeColumnId.value) timeGrain.value = 'MONTH'
}

function buildDimensions(): { asset_column_id: number; time_grain?: string }[] {
  const dims: { asset_column_id: number; time_grain?: string }[] = categoryIds.value.map((id) => ({
    asset_column_id: id,
  }))
  if (timeColumnId.value) {
    dims.push({ asset_column_id: timeColumnId.value, time_grain: timeGrain.value })
  }
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
    })
  } finally {
    previewing.value = false
  }
}

async function onSubmit() {
  if (!assetId.value || !name.value) {
    ElMessage.warning('请选择资产并填写指标名称')
    return
  }
  if (!measureId.value) {
    ElMessage.warning('请选择度量字段')
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
      unit: unit.value,
      cycle: cycle.value,
      caliber_id: caliberId.value,
      owner_name: '',
    })
    ElMessage.success(`已创建草稿 ${created.indicator_code}`)
    router.replace(`/indicators/${created.id}`)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  domains.value = await listDomains()
  calibers.value = (await listCalibers('INDICATOR')) as Caliber[]
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
