<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">数据域</div>
        <div class="page-sub">维护数据域的名称、排序与边界说明；已有资产的域不能删除</div>
      </div>
      <div class="page-actions">
        <el-button :loading="loading" @click="load">刷新</el-button>
        <el-button type="primary" @click="openCreate">新增数据域</el-button>
      </div>
    </div>

    <div class="card table-card">
      <el-table :data="rows" v-loading="loading">
        <el-table-column label="域码" width="110">
          <template #default="{ row }"><span class="mono">{{ row.domain_code }}</span></template>
        </el-table-column>
        <el-table-column prop="domain_name" label="名称" min-width="140" />
        <el-table-column label="已登记资产" width="110" align="right">
          <template #default="{ row }">
            <span :class="{ zero: !row.asset_count }">{{ row.asset_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sort" label="排序" width="80" align="right" />
        <el-table-column prop="description" label="边界说明" min-width="260" show-overflow-tooltip />
        <el-table-column label="操作" width="150" align="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
            <el-tooltip :disabled="!row.asset_count" content="该域下已有资产，不能删除" placement="top">
              <span>
                <el-button size="small" text type="danger" :disabled="row.asset_count > 0" @click="onDelete(row)">
                  删除
                </el-button>
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="card map-card">
      <div class="map-head">
        <div>
          <div class="map-title">
            地图锚点
            <el-tag size="small" type="info" effect="plain">低频</el-tag>
          </div>
          <div class="map-sub">拖动圆点到底图上对应的设施位置，保存后「数据全景」按此定位</div>
        </div>
        <div class="map-actions">
          <template v-if="anchorOpen">
            <el-button @click="resetAnchors">恢复默认</el-button>
            <el-button type="primary" :loading="savingAnchors" @click="saveAnchors">保存锚点</el-button>
          </template>
          <el-button :type="anchorOpen ? 'default' : 'primary'" plain @click="anchorOpen = !anchorOpen">
            {{ anchorOpen ? '收起' : '展开配置' }}
          </el-button>
        </div>
      </div>
      <div v-show="anchorOpen" ref="mapEl" class="map-editor">
        <div
          v-for="d in rows"
          :key="d.domain_code"
          class="pin"
          :class="{ dragging: dragCode === d.domain_code }"
          :style="{ left: pct(anchorOf(d).x), top: pct(anchorOf(d).y) }"
          @pointerdown.prevent="startDrag(d.domain_code)"
        >
          <i :style="{ background: colorOf(d.domain_code) }"></i>
          <span>{{ d.domain_name }}</span>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑数据域' : '新增数据域'" width="520px">
      <el-form :model="form" label-width="90px" label-position="left">
        <el-form-item label="域码" required>
          <el-input v-model="form.domain_code" :disabled="!!form.id" placeholder="3-8 位小写字母，如 fin" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.domain_name" placeholder="如 财务" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" controls-position="right" />
        </el-form-item>
        <el-form-item label="边界说明">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="这个域管什么、不管什么" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createDomain, deleteDomain, listDomains, patchDomain, type Domain } from '@/api/catalog'

const rows = ref<Domain[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const form = reactive<any>({ id: 0, domain_code: '', domain_name: '', sort: 0, description: '' })

const PALETTE = ['#0A84FF', '#12A8D8', '#4F7CFF', '#7C6CF0', '#9B7CFF', '#17A2B8', '#2BB39B', '#5B8DEF', '#E0A23F', '#6FA84F']
const DEFAULT_ANCHORS: Record<string, [number, number]> = {
  prd: [0.273, 0.330], dsp: [0.481, 0.334], net: [0.593, 0.382], mkt: [0.718, 0.208], svc: [0.945, 0.200],
  drn: [0.737, 0.677], wqm: [0.080, 0.752], ast: [0.312, 0.704], prj: [0.478, 0.680], she: [0.910, 0.800],
}
const mapEl = ref<HTMLDivElement | null>(null)
const anchors = reactive<Record<string, { x: number; y: number }>>({})
const savingAnchors = ref(false)
const dragCode = ref('')
const anchorOpen = ref(false)

function colorOf(code: string) {
  const i = rows.value.findIndex((r) => r.domain_code === code)
  return PALETTE[(i < 0 ? 0 : i) % PALETTE.length]
}

function defaultAnchor(code: string): [number, number] {
  return DEFAULT_ANCHORS[code] || [0.5, 0.5]
}

function anchorOf(d: Domain) {
  return anchors[d.domain_code] || { x: d.anchor_x ?? defaultAnchor(d.domain_code)[0], y: d.anchor_y ?? defaultAnchor(d.domain_code)[1] }
}

function pct(v: number) {
  return `${(v * 100).toFixed(2)}%`
}

function syncAnchors() {
  for (const d of rows.value) {
    anchors[d.domain_code] = {
      x: d.anchor_x ?? defaultAnchor(d.domain_code)[0],
      y: d.anchor_y ?? defaultAnchor(d.domain_code)[1],
    }
  }
}

function startDrag(code: string) {
  dragCode.value = code
  window.addEventListener('pointermove', onDrag)
  window.addEventListener('pointerup', endDrag)
}

function onDrag(e: PointerEvent) {
  if (!dragCode.value || !mapEl.value) return
  const rect = mapEl.value.getBoundingClientRect()
  const x = Math.min(0.98, Math.max(0.02, (e.clientX - rect.left) / rect.width))
  const y = Math.min(0.98, Math.max(0.02, (e.clientY - rect.top) / rect.height))
  anchors[dragCode.value] = { x, y }
}

function endDrag() {
  dragCode.value = ''
  window.removeEventListener('pointermove', onDrag)
  window.removeEventListener('pointerup', endDrag)
}

function resetAnchors() {
  for (const d of rows.value) {
    const [x, y] = defaultAnchor(d.domain_code)
    anchors[d.domain_code] = { x, y }
  }
  ElMessage.info('已恢复默认位置，点「保存锚点」生效')
}

async function saveAnchors() {
  savingAnchors.value = true
  try {
    let changed = 0
    for (const d of rows.value) {
      const a = anchors[d.domain_code]
      if (!a) continue
      const nx = Number(a.x.toFixed(4))
      const ny = Number(a.y.toFixed(4))
      if (nx !== d.anchor_x || ny !== d.anchor_y) {
        await patchDomain(d.id, { anchor_x: nx, anchor_y: ny })
        changed += 1
      }
    }
    ElMessage.success(changed ? `已保存 ${changed} 个锚点` : '锚点没有变化')
    await load()
  } finally {
    savingAnchors.value = false
  }
}

async function load() {
  loading.value = true
  try {
    rows.value = await listDomains()
    syncAnchors()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, {
    id: 0,
    domain_code: '',
    domain_name: '',
    sort: (rows.value.length ? Math.max(...rows.value.map((r) => r.sort)) : 0) + 1,
    description: '',
  })
  dialogVisible.value = true
}

function openEdit(row: Domain) {
  Object.assign(form, {
    id: row.id,
    domain_code: row.domain_code,
    domain_name: row.domain_name,
    sort: row.sort,
    description: row.description || '',
  })
  dialogVisible.value = true
}

async function onSave() {
  if (!form.domain_name || !form.domain_code) {
    ElMessage.warning('请填写域码与名称')
    return
  }
  saving.value = true
  try {
    if (form.id) {
      await patchDomain(form.id, {
        domain_name: form.domain_name,
        sort: form.sort,
        description: form.description || null,
      })
      ElMessage.success('已保存')
    } else {
      await createDomain({
        domain_code: form.domain_code.trim().toLowerCase(),
        domain_name: form.domain_name,
        sort: form.sort,
        description: form.description || null,
      })
      ElMessage.success('已新增')
    }
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function onDelete(row: Domain) {
  await ElMessageBox.confirm(
    `确认删除数据域「${row.domain_name}」（${row.domain_code}）？`,
    '删除确认',
    { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' },
  )
  await deleteDomain(row.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<style scoped>
.table-card {
  padding: 6px 4px;
  overflow: hidden;
}
.zero {
  color: var(--color-text-secondary);
}
.map-card { padding: 16px 18px; margin-bottom: 16px; }
.map-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 12px; }
.map-title { font-size: 15px; font-weight: 600; }
.map-sub { font-size: 12px; color: var(--color-text-secondary); margin-top: 2px; }
.map-editor {
  position: relative;
  width: 100%;
  aspect-ratio: 2048 / 1152;
  background: url('/water-cycle.png') center / 100% 100% no-repeat;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
}
.pin {
  position: absolute;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #DCEBFA;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: grab;
  user-select: none;
  box-shadow: 0 2px 8px rgba(10, 132, 255, 0.12);
  white-space: nowrap;
}
.pin i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.pin.dragging { cursor: grabbing; box-shadow: 0 4px 16px rgba(10, 132, 255, 0.32); }
</style>
