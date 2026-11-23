<template>
  <div>
    <div class="page-header">
      <div>
        <el-button link type="primary" @click="$router.push('/indicators')">← 返回指标中心</el-button>
        <div class="page-title">新建指标</div>
        <div class="page-sub">指标必须从已登记的资产字段创建，来源字段不可手填</div>
      </div>
    </div>

    <el-form :model="form" label-width="110px" class="card form-card" v-loading="loading">
      <el-form-item label="数据域" required>
        <el-select v-model="form.domain_code" style="width: 240px" placeholder="先选数据域" @change="onDomainChange">
          <el-option v-for="d in domains" :key="d.domain_code" :label="d.domain_name" :value="d.domain_code" />
        </el-select>
      </el-form-item>
      <el-form-item label="来源资产" required>
        <el-select v-model="form.asset_id" style="width: 360px" placeholder="选择该域下的资产" filterable :disabled="!form.domain_code" @change="onAssetChange">
          <el-option v-for="a in assets" :key="a.id" :label="`${a.asset_name}（${a.table_name}）`" :value="a.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="来源字段" required>
        <el-select v-model="form.source_asset_column_id" style="width: 360px" placeholder="选择字段" filterable :disabled="!form.asset_id">
          <el-option v-for="c in columns" :key="c.id" :label="`${c.column_name}　${c.business_name || c.column_comment || ''}`" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="指标名称" required><el-input v-model="form.indicator_name" style="width: 360px" /></el-form-item>
      <el-form-item label="指标编码">
        <el-input v-model="form.indicator_code" style="width: 240px" placeholder="留空自动生成，如 BM03031" />
      </el-form-item>
      <el-form-item label="指标定义"><el-input v-model="form.indicator_def" type="textarea" :rows="2" /></el-form-item>
      <el-form-item label="计算公式" required><el-input v-model="form.formula" placeholder="如 receivable_amount / received_amount" /></el-form-item>
      <el-form-item label="单位" required>
        <el-select v-model="form.unit" style="width: 160px" placeholder="选择单位">
          <el-option v-for="u in UNITS" :key="u" :label="u" :value="u" />
        </el-select>
      </el-form-item>
      <el-form-item label="累计周期" required>
        <el-select v-model="form.cycle" style="width: 160px">
          <el-option label="日" value="日" />
          <el-option label="月" value="月" />
          <el-option label="年" value="年" />
        </el-select>
      </el-form-item>
      <el-form-item label="关联口径">
        <el-select v-model="form.caliber_id" clearable style="width: 360px" placeholder="可选，校验仅提示">
          <el-option v-for="c in calibers" :key="c.id" :label="`${c.caliber_code} ${c.caliber_name}`" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="责任人"><el-input v-model="form.owner_name" style="width: 240px" /></el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="onSubmit">创建草稿</el-button>
        <span class="hint">创建后进入草稿，校验通过才可发布</span>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getAsset, listAssets, listDomains, type Asset, type AssetColumn, type Domain } from '@/api/catalog'
import { createIndicator, listCalibers, type Caliber } from '@/api/indicator'

const route = useRoute()
const router = useRouter()
const domains = ref<Domain[]>([])
const assets = ref<Asset[]>([])
const columns = ref<AssetColumn[]>([])
const calibers = ref<Caliber[]>([])
const loading = ref(false)
const saving = ref(false)
const UNITS = ['%', '元', 'm³', '户', '个', '次', '小时', '分钟', '秒', '元/m³']

const form = reactive<any>({
  domain_code: '',
  asset_id: null,
  source_asset_column_id: null,
  indicator_code: '',
  indicator_name: '',
  indicator_def: '',
  formula: '',
  unit: '%',
  cycle: '月',
  caliber_id: null,
  owner_name: '',
})

async function loadAssets() {
  if (!form.domain_code) {
    assets.value = []
    return
  }
  const res = await listAssets({ domain_code: form.domain_code, page_size: 200 })
  assets.value = res.items
}

async function onDomainChange() {
  form.asset_id = null
  form.source_asset_column_id = null
  columns.value = []
  await loadAssets()
}

async function onAssetChange() {
  form.source_asset_column_id = null
  if (!form.asset_id) return
  const detail = await getAsset(form.asset_id)
  columns.value = detail.columns
}

async function preset() {
  const assetId = Number(route.query.asset || 0)
  const columnId = Number(route.query.column || 0)
  if (!assetId) return
  loading.value = true
  try {
    const detail = await getAsset(assetId)
    form.domain_code = detail.domain_code || ''
    await loadAssets()
    form.asset_id = detail.id
    columns.value = detail.columns
    if (columnId) form.source_asset_column_id = columnId
  } finally {
    loading.value = false
  }
}

async function onSubmit() {
  if (!form.source_asset_column_id || !form.indicator_name || !form.formula) {
    ElMessage.warning('请选择来源字段并填写名称、公式')
    return
  }
  saving.value = true
  try {
    const created = await createIndicator({
      ...form,
      indicator_code: form.indicator_code || null,
      caliber_id: form.caliber_id || null,
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
  await preset()
})
</script>

<style scoped>
.form-card {
  padding: 20px 24px;
  max-width: 900px;
}
.hint {
  margin-left: 12px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
</style>
