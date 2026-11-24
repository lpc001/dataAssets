<template>
  <div class="data-map">
    <header class="top">
      <div class="title-block">
        <div class="title">数据全景</div>
        <div class="subtitle">按数据域组织的资产星图 · 发现、定位、下钻</div>
      </div>
      <div class="kpis">
        <div class="kpi" v-for="k in kpis" :key="k.label">
          <div class="kpi-value">{{ k.value }}</div>
          <div class="kpi-label">{{ k.label }}</div>
        </div>
      </div>
      <div class="tools">
        <div class="switch">
          <button v-for="v in views" :key="v.key" :class="{ active: view === v.key }" @click="setView(v.key)">
            {{ v.label }}
          </button>
        </div>
        <input v-model="keyword" class="search" placeholder="搜索资产名称 / 编码 / 表名" />
      </div>
    </header>

    <main class="stage-wrap">
      <div class="stage">
        <div v-show="view !== 'city'" ref="chartEl" class="chart"></div>
        <canvas
          v-show="view === 'city'"
          ref="canvasEl"
          class="city"
          @click="onCanvasClick"
          @mousemove="onCanvasMove"
          @mouseleave="hoverAsset = null"
        ></canvas>

        <div class="focus-chip" v-if="focusDomain">
          已聚焦：{{ domainName(focusDomain) }}
          <button @click="focusDomain = ''">返回全域</button>
        </div>

        <div class="empty-tip" v-if="!loading && !visibleAssets.length">没有匹配的资产</div>
      </div>

      <aside class="detail" v-if="current">
        <div class="detail-close" @click="current = null">×</div>
        <div class="detail-domain">{{ domainName(current.domain_code) }} · {{ layerLabel(current.layer) }}</div>
        <div class="detail-name">{{ current.asset_name }}</div>
        <div class="detail-code">{{ current.asset_code }} · {{ current.table_name }}</div>
        <div class="detail-grid">
          <div><span>行数</span>{{ fmtNumber(current.rows) }}</div>
          <div><span>字段</span>{{ current.columns }}</div>
          <div><span>状态</span>{{ current.status === 'PUBLISHED' ? '已发布' : '未发布' }}</div>
          <div><span>归类</span>{{ groupLabel(current.group_type) }}</div>
        </div>
        <div class="detail-actions">
          <button class="primary" @click="$router.push(`/catalog/${current.id}`)">查看资产详情</button>
          <button @click="$router.push(`/catalog/${current.id}`)">数据预览</button>
        </div>
      </aside>
    </main>

    <footer class="legend">
      <button
        v-for="d in data.domains"
        :key="d.domain_code"
        class="legend-item"
        :class="{ dim: focusDomain && focusDomain !== d.domain_code }"
        @click="toggleDomain(d.domain_code)"
      >
        <i :style="{ background: colorOf(d.domain_code) }"></i>
        {{ d.domain_name }}<em>{{ d.asset_count }}</em>
      </button>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { fetchDataMap, type DataMap, type MapAsset } from '@/api/catalog'

const PALETTE = ['#3DD6F5', '#7C6CFF', '#FF7AC6', '#4FE3A1', '#FFC457', '#FF8A5B', '#5AA9FF', '#B98BFF', '#3EDBD3', '#F26D85']

const data = ref<DataMap>({ domain_count: 0, asset_count: 0, column_count: 0, published_count: 0, domains: [], assets: [] })
const loading = ref(true)
const view = ref<'star' | 'matrix' | 'city'>('star')
const keyword = ref('')
const focusDomain = ref('')
const current = ref<MapAsset | null>(null)
const hoverAsset = ref<MapAsset | null>(null)

const chartEl = ref<HTMLDivElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)
let chart: echarts.ECharts | null = null
let cityHits: { asset: MapAsset; x: number; y: number; w: number; h: number }[] = []

const views = [
  { key: 'star', label: '星图' },
  { key: 'matrix', label: '矩阵' },
  { key: 'city', label: '城市' },
] as const

const kpis = computed(() => [
  { label: '数据域', value: data.value.domain_count },
  { label: '资产', value: data.value.asset_count },
  { label: '字段', value: data.value.column_count },
  { label: '已发布', value: data.value.published_count },
])

const domainColor = computed(() => {
  const map: Record<string, string> = {}
  data.value.domains.forEach((d, i) => (map[d.domain_code] = PALETTE[i % PALETTE.length]))
  return map
})

function colorOf(code: string | null) {
  if (!code) return '#5B7083'
  return domainColor.value[code] || '#5B7083'
}

function domainName(code: string | null) {
  if (!code) return '公共'
  return data.value.domains.find((d) => d.domain_code === code)?.domain_name || code
}

function layerLabel(layer: string | null) {
  return { DIM: '维度数据', DWD: '业务数据', DWS: '汇总统计' }[layer || ''] || '其他'
}

function groupLabel(group: string) {
  return { DOMAIN: '业务域', PUBLIC: '公共维度', TOPIC: '跨域专题', OTHER: '未归类' }[group] || group
}

function fmtNumber(value: number | null) {
  if (value === null || value === undefined) return '—'
  if (value >= 10000) return (value / 10000).toFixed(1) + ' 万'
  return String(value)
}

const visibleAssets = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return data.value.assets.filter((a) => {
    if (a.status !== 'PUBLISHED') return false
    if (focusDomain.value && a.domain_code !== focusDomain.value) return false
    if (!kw) return true
    return (
      a.asset_name.toLowerCase().includes(kw) ||
      (a.asset_code || '').toLowerCase().includes(kw) ||
      a.table_name.toLowerCase().includes(kw)
    )
  })
})

function setView(next: 'star' | 'matrix' | 'city') {
  view.value = next
  current.value = null
  nextTick(() => (next === 'city' ? drawCity() : renderChart()))
}

function toggleDomain(code: string) {
  focusDomain.value = focusDomain.value === code ? '' : code
}

function onAssetClick(asset: MapAsset) {
  current.value = asset
}

// ---------------- star / matrix ----------------
function starOption() {
  const assets = visibleAssets.value
  const nodes: any[] = []
  const links: any[] = []
  const activeDomains = new Set(assets.map((a) => a.domain_code || 'public'))

  data.value.domains.forEach((d) => {
    if (!activeDomains.has(d.domain_code) && d.asset_count === 0) {
      nodes.push({
        id: 'd:' + d.domain_code,
        name: d.domain_name,
        symbolSize: 14,
        itemStyle: { color: colorOf(d.domain_code), opacity: 0.28 },
        label: { show: true, color: 'rgba(220, 235, 255, 0.45)', fontSize: 11 },
        category: 'domain',
      })
      return
    }
    nodes.push({
      id: 'd:' + d.domain_code,
      name: d.domain_name,
      symbolSize: 30 + Math.min(26, Math.sqrt(d.asset_count) * 8),
      itemStyle: { color: colorOf(d.domain_code), shadowBlur: 30, shadowColor: colorOf(d.domain_code) },
      label: { show: true, color: '#E6F4FF', fontSize: 13, fontWeight: 600 },
      category: 'domain',
    })
  })
  assets.forEach((a) => {
    nodes.push({
      id: 'a:' + a.id,
      name: a.asset_name,
      symbolSize: 6 + Math.min(12, Math.sqrt(a.rows || 0) / 8),
      itemStyle: { color: colorOf(a.domain_code), opacity: 0.85, shadowBlur: 12, shadowColor: colorOf(a.domain_code) },
      label: { show: false },
      category: 'asset',
      asset: a,
    })
    links.push({
      source: 'd:' + (a.domain_code || 'public'),
      target: 'a:' + a.id,
      lineStyle: { color: colorOf(a.domain_code), opacity: 0.25, width: 1 },
    })
  })

  return {
    backgroundColor: '#06121f',
    tooltip: {
      backgroundColor: 'rgba(8, 24, 40, 0.92)',
      borderColor: 'rgba(61, 214, 245, 0.35)',
      textStyle: { color: '#DCEBFF', fontSize: 12 },
      formatter: (p: any) => {
        const a = p.data?.asset
        if (!a) return p.name
        return `${a.asset_name}<br/>${a.table_name}<br/>行数 ${fmtNumber(a.rows)} · 字段 ${a.columns}`
      },
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        force: { repulsion: 220, edgeLength: [40, 120], gravity: 0.08 },
        emphasis: { focus: 'adjacency', lineStyle: { opacity: 0.7 } },
        data: nodes,
        links,
        lineStyle: { curveness: 0.15 },
      },
    ],
  }
}

function matrixOption() {
  const assets = visibleAssets.value
  const children = data.value.domains
    .map((d) => {
      const items = assets.filter((a) => a.domain_code === d.domain_code)
      if (!items.length) return null
      return {
        name: d.domain_name,
        value: items.reduce((s, a) => s + Math.max(a.rows || 0, 1), 0),
        itemStyle: { color: colorOf(d.domain_code) },
        children: items.map((a) => ({
          name: a.asset_name,
          value: Math.max(a.rows || 0, 1),
          asset: a,
          itemStyle: { color: colorOf(a.domain_code), opacity: 0.72 },
        })),
      }
    })
    .filter(Boolean)

  return {
    backgroundColor: '#06121f',
    tooltip: {
      backgroundColor: 'rgba(8, 24, 40, 0.92)',
      borderColor: 'rgba(61, 214, 245, 0.35)',
      textStyle: { color: '#DCEBFF', fontSize: 12 },
      formatter: (p: any) => {
        const a = p.data?.asset
        if (!a) return p.name
        return `${a.asset_name}<br/>${a.table_name}<br/>行数 ${fmtNumber(a.rows)}`
      },
    },
    series: [
      {
        type: 'treemap',
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        width: '96%',
        height: '92%',
        top: '4%',
        left: '2%',
        label: { color: '#F2F9FF', fontSize: 12 },
        upperLabel: { show: true, color: '#CFE9FF', fontSize: 13, height: 22 },
        itemStyle: { borderColor: 'rgba(6, 18, 31, 0.85)', borderWidth: 2, gapWidth: 2 },
        levels: [
          { itemStyle: { borderWidth: 0, gapWidth: 4 } },
          { itemStyle: { borderWidth: 1, gapWidth: 2 } },
        ],
        data: children,
      },
    ],
  }
}

function renderChart() {
  if (!chartEl.value) return
  if (!chart) chart = echarts.init(chartEl.value)
  chart.setOption(view.value === 'matrix' ? matrixOption() : starOption(), true)
  chart.off('click')
  chart.on('click', (p: any) => {
    if (p.data?.asset) onAssetClick(p.data.asset)
    else if (p.data?.id?.toString().startsWith('d:')) {
      focusDomain.value = p.data.id.slice(2)
    }
  })
}

// ---------------- city ----------------
function drawCity() {
  const canvas = canvasEl.value
  if (!canvas) return
  const rect = canvas.parentElement!.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  canvas.style.width = rect.width + 'px'
  canvas.style.height = rect.height + 'px'
  const ctx = canvas.getContext('2d')!
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  const bg = ctx.createLinearGradient(0, 0, 0, rect.height)
  bg.addColorStop(0, '#081726')
  bg.addColorStop(1, '#04101a')
  ctx.fillStyle = bg
  ctx.fillRect(0, 0, rect.width, rect.height)

  cityHits = []

  const domains = data.value.domains
  const cols = 5
  const rows = Math.ceil(domains.length / cols)
  const pad = 20
  const cellW = (rect.width - pad * 2) / cols
  const cellH = (rect.height - pad * 2) / rows

  domains.forEach((domain, di) => {
    const originX = pad + (di % cols) * cellW
    const originY = pad + Math.floor(di / cols) * cellH
    const items = visibleAssets.value
      .filter((a) => a.domain_code === domain.domain_code)
      .sort((a, b) => (b.rows || 0) - (a.rows || 0))
    const color = colorOf(domain.domain_code)

    const pw = cellW * 0.9
    const ph = cellH * 0.86
    const px = originX + (cellW - pw) / 2
    const py = originY + (cellH - ph) / 2

    // 平台底板
    ctx.beginPath()
    ctx.roundRect(px, py, pw, ph, 12)
    ctx.fillStyle = 'rgba(9, 28, 45, 0.55)'
    ctx.fill()
    ctx.strokeStyle = color
    ctx.globalAlpha = items.length ? 0.3 : 0.14
    ctx.lineWidth = 1
    ctx.stroke()
    ctx.globalAlpha = 1

    // 平台内标题
    ctx.save()
    ctx.beginPath()
    ctx.rect(px, py, pw, ph)
    ctx.clip()
    ctx.textAlign = 'left'
    ctx.font = '13px "PingFang SC", sans-serif'
    ctx.fillStyle = items.length ? 'rgba(230, 244, 255, 0.95)' : 'rgba(180, 205, 225, 0.45)'
    ctx.fillText(domain.domain_name, px + 12, py + 20, pw - 24)
    ctx.font = '11px "PingFang SC", sans-serif'
    ctx.fillStyle = items.length ? color : 'rgba(140, 170, 195, 0.45)'
    ctx.fillText(`${items.length} 个资产`, px + 12, py + 36, pw - 24)

    if (!items.length) {
      ctx.restore()
      return
    }

    // 天际线：每域最多 10 栋，按行数排序
    const shown = items.slice(0, 10)
    const overflow = items.length - shown.length
    const maxRows = Math.max(...shown.map((a) => a.rows || 0), 1)
    const baseY = py + ph - 26
    const maxH = ph * 0.56
    const areaW = pw - 28
    const slot = areaW / shown.length
    const bw = Math.min(26, slot * 0.6)

    shown.forEach((asset, ai) => {
      const bx = px + 14 + ai * slot + (slot - bw) / 2
      const height = 8 + Math.sqrt((asset.rows || 0) / maxRows) * maxH

      // 阴影
      ctx.fillStyle = 'rgba(3, 10, 18, 0.75)'
      ctx.fillRect(bx + 3, baseY - height + 4, bw, height)
      // 建筑主体
      ctx.fillStyle = color
      ctx.globalAlpha = 0.92
      ctx.fillRect(bx, baseY - height, bw, height)
      // 顶面
      ctx.globalAlpha = 0.5
      ctx.beginPath()
      ctx.moveTo(bx, baseY - height)
      ctx.lineTo(bx + bw * 0.22, baseY - height - bw * 0.2)
      ctx.lineTo(bx + bw * 1.22, baseY - height - bw * 0.2)
      ctx.lineTo(bx + bw, baseY - height)
      ctx.closePath()
      ctx.fill()
      // 楼基
      ctx.globalAlpha = 1
      ctx.fillStyle = 'rgba(3, 10, 18, 0.9)'
      ctx.fillRect(bx, baseY, bw, 6)

      cityHits.push({ asset, x: bx, y: baseY - height, w: bw + 4, h: height + 8 })
    })

    if (overflow > 0) {
      ctx.textAlign = 'right'
      ctx.font = '11px "PingFang SC", sans-serif'
      ctx.fillStyle = 'rgba(160, 195, 220, 0.75)'
      ctx.fillText(`+${overflow}`, px + pw - 12, py + ph - 12)
    }
    ctx.restore()
  })
}

function onCanvasClick(e: MouseEvent) {
  const rect = (e.target as HTMLElement).getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  const hit = cityHits.find((h) => x >= h.x && x <= h.x + h.w && y >= h.y && y <= h.y + h.h + 8)
  if (hit) current.value = hit.asset
}

function onCanvasMove(e: MouseEvent) {
  const rect = (e.target as HTMLElement).getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  const hit = cityHits.find((h) => x >= h.x && x <= h.x + h.w && y >= h.y && y <= h.y + h.h + 8)
  hoverAsset.value = hit?.asset || null
  const canvas = canvasEl.value
  if (canvas) canvas.style.cursor = hit ? 'pointer' : 'default'
}

// ---------------- lifecycle ----------------
let resizeObserver: ResizeObserver | null = null

async function load() {
  loading.value = true
  try {
    data.value = await fetchDataMap()
  } finally {
    loading.value = false
    await nextTick()
    renderChart()
  }
}

watch([keyword, focusDomain], () => {
  current.value = null
  if (view.value === 'city') drawCity()
  else renderChart()
})

onMounted(async () => {
  await load()
  if (chartEl.value) {
    resizeObserver = new ResizeObserver(() => {
      chart?.resize()
      if (view.value === 'city') drawCity()
    })
    resizeObserver.observe(chartEl.value.parentElement as Element)
  }
})

onBeforeUnmount(() => {
  chart?.dispose()
  resizeObserver?.disconnect()
})
</script>

<style scoped>
.data-map {
  position: relative;
  margin: -22px -26px;
  min-height: calc(100vh - 0px);
  padding: 22px 26px 18px;
  background:
    radial-gradient(1200px 600px at 20% -10%, rgba(10, 132, 255, 0.18), transparent 60%),
    radial-gradient(900px 500px at 90% 10%, rgba(124, 108, 255, 0.14), transparent 55%),
    linear-gradient(180deg, #06121f 0%, #04101a 100%);
  color: #DCEBFF;
  border-radius: 16px;
}
.top { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; flex-wrap: wrap; }
.title { font-size: 24px; font-weight: 700; letter-spacing: 0.02em; }
.subtitle { margin-top: 4px; font-size: 12.5px; color: #7FA3C4; }
.kpis { display: flex; gap: 26px; }
.kpi-value { font-size: 26px; font-weight: 700; color: #EAF6FF; font-variant-numeric: tabular-nums; text-shadow: 0 0 18px rgba(61, 214, 245, 0.45); }
.kpi-label { font-size: 12px; color: #7FA3C4; margin-top: 2px; }
.tools { display: flex; align-items: center; gap: 12px; }
.switch { display: inline-flex; background: rgba(10, 30, 48, 0.7); border: 1px solid rgba(61, 214, 245, 0.22); border-radius: 10px; padding: 3px; }
.switch button { background: transparent; border: 0; color: #8FB6D6; padding: 6px 14px; font-size: 12.5px; border-radius: 8px; cursor: pointer; }
.switch button.active { background: linear-gradient(135deg, rgba(61, 214, 245, 0.28), rgba(10, 132, 255, 0.35)); color: #EAF6FF; }
.search { width: 240px; background: rgba(10, 30, 48, 0.7); border: 1px solid rgba(61, 214, 245, 0.22); border-radius: 10px; padding: 8px 12px; color: #DCEBFF; outline: none; font-size: 12.5px; }
.search::placeholder { color: #5F86A6; }
.stage-wrap { display: flex; gap: 16px; margin-top: 16px; align-items: stretch; }
.stage { position: relative; flex: 1; min-width: 0; height: calc(100vh - 230px); min-height: 460px; background: rgba(7, 22, 36, 0.55); border: 1px solid rgba(61, 214, 245, 0.14); border-radius: 16px; overflow: hidden; }
.chart, .city { width: 100%; height: 100%; display: block; }
.focus-chip { position: absolute; top: 14px; left: 16px; background: rgba(10, 30, 48, 0.85); border: 1px solid rgba(61, 214, 245, 0.3); padding: 6px 12px; border-radius: 999px; font-size: 12.5px; }
.focus-chip button { margin-left: 10px; background: transparent; border: 0; color: #3DD6F5; cursor: pointer; font-size: 12.5px; }
.empty-tip { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #6E93B4; font-size: 13px; }
.detail { width: 300px; flex-shrink: 0; background: rgba(9, 26, 42, 0.9); border: 1px solid rgba(61, 214, 245, 0.22); border-radius: 16px; padding: 18px; position: relative; backdrop-filter: blur(8px); }
.detail-close { position: absolute; right: 14px; top: 10px; color: #6E93B4; cursor: pointer; font-size: 18px; }
.detail-domain { font-size: 12px; color: #3DD6F5; }
.detail-name { margin-top: 6px; font-size: 18px; font-weight: 700; line-height: 1.4; }
.detail-code { margin-top: 4px; font-size: 11.5px; color: #7FA3C4; word-break: break-all; }
.detail-grid { margin-top: 16px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.detail-grid div { font-size: 13px; color: #DCEBFF; }
.detail-grid span { display: block; font-size: 11.5px; color: #6E93B4; margin-bottom: 2px; }
.detail-actions { margin-top: 20px; display: flex; flex-direction: column; gap: 8px; }
.detail-actions button { background: rgba(10, 30, 48, 0.9); border: 1px solid rgba(61, 214, 245, 0.28); color: #CFE9FF; padding: 9px 12px; border-radius: 10px; cursor: pointer; font-size: 13px; }
.detail-actions button.primary { background: linear-gradient(135deg, rgba(61, 214, 245, 0.35), rgba(10, 132, 255, 0.5)); border-color: transparent; color: #F2FAFF; font-weight: 600; }
.legend { margin-top: 14px; display: flex; flex-wrap: wrap; gap: 8px; padding-bottom: 4px; }
.legend-item { display: inline-flex; align-items: center; gap: 7px; background: rgba(9, 26, 42, 0.7); border: 1px solid rgba(61, 214, 245, 0.16); color: #A9CBE6; border-radius: 999px; padding: 5px 12px; font-size: 12px; cursor: pointer; }
.legend-item i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; box-shadow: 0 0 10px currentColor; }
.legend-item em { font-style: normal; color: #5F86A6; }
.legend-item.dim { opacity: 0.35; }
</style>
