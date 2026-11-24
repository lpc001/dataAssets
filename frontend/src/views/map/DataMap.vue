<template>
  <div class="data-map">
    <header class="top">
      <div class="title-block">
        <div class="title">数据全景</div>
        <div class="subtitle">从源头到龙头的水脉视图 · 发现、定位、下钻</div>
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
        <WaterCycleBg class="water-bg" />
        <div class="veil"></div>
        <div v-show="view !== 'city'" ref="chartEl" class="chart"></div>
        <canvas
          v-show="view === 'city'"
          ref="canvasEl"
          class="city"
          @click="onCanvasClick"
          @mousemove="onCanvasMove"
          @mouseleave="hoverAsset = null"
        ></canvas>

        <div class="river-legend" v-if="view === 'water'">
          <span>源头</span><i></i><span>制水</span><i></i><span>输配</span><i></i><span>计量收费</span><i></i><span>服务</span><i></i><span>排水</span>
        </div>

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
import WaterCycleBg from '@/components/WaterCycleBg.vue'

// 品牌蓝为锚点，向青/紫/绿/琥珀发散的水务谱系：既有区分度，又不会全蓝疲劳
const PALETTE = ['#0A84FF', '#12A8D8', '#4F7CFF', '#7C6CF0', '#9B7CFF', '#17A2B8', '#2BB39B', '#5B8DEF', '#E0A23F', '#6FA84F']
const GROUP_COLORS: Record<string, string> = { PUBLIC: '#7FA3C4', TOPIC: '#6C8CFF', OTHER: '#8FA8C4', DOMAIN: '#0A84FF' }

// 水务价值链顺序：源头 → 制水 → 输配 → 计量收费 → 服务 → 排水
// 锚点与底图设施一一对应（水厂/泵站/管网/城市/客服/污水厂/监测点/维护基地/工地/排放口）
const CHAIN_POS: Record<string, [number, number]> = {
  prd: [0.355, 0.17],
  dsp: [0.44, 0.52],
  net: [0.53, 0.35],
  mkt: [0.66, 0.35],
  svc: [0.84, 0.32],
  drn: [0.67, 0.67],
}
const EXTRA_POS: Record<string, [number, number]> = {
  wqm: [0.097, 0.70],
  ast: [0.373, 0.72],
  prj: [0.537, 0.73],
  she: [0.85, 0.69],
}

const data = ref<DataMap>({ domain_count: 0, asset_count: 0, column_count: 0, published_count: 0, domains: [], assets: [] })
const loading = ref(true)
const view = ref<'water' | 'matrix' | 'city'>('water')
const keyword = ref('')
const focusDomain = ref('')
const current = ref<MapAsset | null>(null)
const hoverAsset = ref<MapAsset | null>(null)

const chartEl = ref<HTMLDivElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)
let chart: echarts.ECharts | null = null
let cityHits: { asset: MapAsset; x: number; y: number; w: number; h: number }[] = []

const views = [
  { key: 'water', label: '水脉' },
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
  if (!code) return '#7FA3C4'
  return domainColor.value[code] || '#7FA3C4'
}

function assetColor(asset: MapAsset) {
  if (asset.domain_code) return colorOf(asset.domain_code)
  return GROUP_COLORS[asset.group_type] || '#7FA3C4'
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

function setView(next: 'water' | 'matrix' | 'city') {
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

// ---------------- 水脉视图 ----------------
function waterOption() {
  const width = chartEl.value?.clientWidth || 900
  const height = chartEl.value?.clientHeight || 520
  const nodes: any[] = []
  const links: any[] = []
  const assets = visibleAssets.value

  data.value.domains.forEach((d) => {
    const pos = CHAIN_POS[d.domain_code] || EXTRA_POS[d.domain_code] || [0.5, 0.5]
    const x = pos[0] * width
    const y = pos[1] * height
    const empty = d.asset_count === 0
    nodes.push({
      id: 'd:' + d.domain_code,
      name: d.domain_name,
      x,
      y,
      symbol: 'circle',
      symbolSize: empty ? 8 : 18 + Math.min(20, Math.sqrt(d.asset_count) * 5),
      itemStyle: {
        color: empty ? 'rgba(10, 132, 255, 0.12)' : colorOf(d.domain_code),
        shadowBlur: empty ? 0 : 18,
        shadowColor: 'rgba(10, 132, 255, 0.35)',
        borderColor: empty ? 'rgba(10, 132, 255, 0.25)' : 'rgba(255, 255, 255, 0.9)',
        borderWidth: empty ? 1 : 2,
      },
      label: {
        show: true,
        position: 'bottom',
        distance: empty ? 4 : 12,
        color: empty ? 'rgba(15, 43, 70, 0.32)' : '#0F2B46',
        fontSize: empty ? 11 : 12,
        fontWeight: empty ? 400 : 600,
      },
    })

    const items = assets.filter((a) => a.domain_code === d.domain_code)
    const angleStep = (Math.PI * 2) / Math.max(items.length, 1)
    items.forEach((a, i) => {
      const radius = 46 + Math.sqrt(i) * 9
      const angle = i * angleStep + (d.domain_code.length % 3) * 0.4
      nodes.push({
        id: 'a:' + a.id,
        name: a.asset_name,
        x: x + Math.cos(angle) * radius,
        y: y + Math.sin(angle) * radius,
        symbolSize: 5 + Math.min(9, Math.sqrt(a.rows || 0) / 9),
        itemStyle: { color: assetColor(a), opacity: 0.8 },
        label: { show: false },
        asset: a,
      })
      links.push({
        source: 'd:' + d.domain_code,
        target: 'a:' + a.id,
        lineStyle: { color: 'rgba(10, 132, 255, 0.18)', width: 1, curveness: 0.12 },
      })
    })
  })

  // 零散的无域资产（公共维度等）放在下方作为“水系外环”
  const others = assets.filter((a) => !a.domain_code)
  others.forEach((a, i) => {
    const x = width * 0.5 + (i - others.length / 2) * 14
    const y = height * 0.95
    nodes.push({
      id: 'a:' + a.id,
      name: a.asset_name,
      x,
      y,
      symbolSize: 5,
      itemStyle: { color: GROUP_COLORS[a.group_type], opacity: 0.7 },
      label: { show: false },
      asset: a,
    })
  })

  return {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: 'rgba(10, 132, 255, 0.25)',
      textStyle: { color: '#0F2B46', fontSize: 12 },
      formatter: (p: any) => {
        const a = p.data?.asset
        if (!a) return p.name
        return `${a.asset_name}<br/>${a.table_name}<br/>行数 ${fmtNumber(a.rows)} · 字段 ${a.columns}`
      },
    },
    series: [
      {
        type: 'graph',
        layout: 'none',
        roam: true,
        data: nodes,
        links,
        emphasis: { focus: 'adjacency' },
        lineStyle: { opacity: 0.9 },
      },
    ],
  }
}

// ---------------- 矩阵 ----------------
function matrixOption() {
  const assets = visibleAssets.value
  const children = data.value.domains
    .map((d) => {
      const items = assets.filter((a) => a.domain_code === d.domain_code)
      if (!items.length) return null
      return {
        name: d.domain_name,
        value: items.reduce((s, a) => s + Math.max(a.rows || 0, 1), 0),
        itemStyle: { color: colorOf(d.domain_code), opacity: 0.85 },
        children: items.map((a) => ({
          name: a.asset_name,
          value: Math.max(a.rows || 0, 1),
          asset: a,
          itemStyle: { color: assetColor(a), opacity: 0.55 },
        })),
      }
    })
    .filter(Boolean)

  return {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: 'rgba(10, 132, 255, 0.25)',
      textStyle: { color: '#0F2B46', fontSize: 12 },
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
        label: { color: '#0F2B46', fontSize: 12 },
        upperLabel: { show: true, color: '#0F2B46', fontSize: 13, height: 22 },
        itemStyle: { borderColor: 'rgba(255, 255, 255, 0.9)', borderWidth: 2, gapWidth: 2 },
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
  const option = view.value === 'matrix' ? matrixOption() : waterOption()
  chart.setOption(option, true)
  chart.off('click')
  chart.on('click', (p: any) => {
    if (p.data?.asset) onAssetClick(p.data.asset)
    else if (p.data?.id?.toString().startsWith('d:')) {
      focusDomain.value = p.data.id.slice(2)
    }
  })
}

// ---------------- 城市 ----------------
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
  bg.addColorStop(0, '#F7FBFF')
  bg.addColorStop(1, '#E8F3FE')
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

    ctx.beginPath()
    ctx.roundRect(px, py, pw, ph, 12)
    ctx.fillStyle = items.length ? 'rgba(255, 255, 255, 0.92)' : 'rgba(255, 255, 255, 0.55)'
    ctx.fill()
    ctx.strokeStyle = color
    ctx.globalAlpha = items.length ? 0.35 : 0.15
    ctx.lineWidth = 1
    ctx.stroke()
    ctx.globalAlpha = 1

    ctx.save()
    ctx.beginPath()
    ctx.rect(px, py, pw, ph)
    ctx.clip()
    ctx.textAlign = 'left'
    ctx.font = '13px "PingFang SC", sans-serif'
    ctx.fillStyle = items.length ? '#0F2B46' : 'rgba(15, 43, 70, 0.35)'
    ctx.fillText(domain.domain_name, px + 12, py + 20, pw - 24)
    ctx.font = '11px "PingFang SC", sans-serif'
    ctx.fillStyle = items.length ? color : 'rgba(15, 43, 70, 0.3)'
    ctx.fillText(`${items.length} 个资产`, px + 12, py + 36, pw - 24)

    if (!items.length) {
      ctx.restore()
      return
    }

    const shown = items.slice(0, 10)
    const overflow = items.length - shown.length
    const maxRows = Math.max(...shown.map((a) => a.rows || 0), 1)
    const baseY = py + ph - 26
    const maxH = ph * 0.52
    const areaW = pw - 28
    const slot = areaW / shown.length
    const bw = Math.min(26, slot * 0.6)

    shown.forEach((asset, ai) => {
      const bx = px + 14 + ai * slot + (slot - bw) / 2
      const height = 8 + Math.sqrt((asset.rows || 0) / maxRows) * maxH
      const g = ctx.createLinearGradient(bx, baseY - height, bx, baseY)
      g.addColorStop(0, 'rgba(255, 255, 255, 0.9)')
      g.addColorStop(1, color)
      ctx.fillStyle = g
      ctx.globalAlpha = 0.9
      ctx.fillRect(bx, baseY - height, bw, height)
      ctx.globalAlpha = 1
      ctx.fillStyle = 'rgba(10, 132, 255, 0.12)'
      ctx.fillRect(bx, baseY, bw, 5)

      cityHits.push({ asset, x: bx, y: baseY - height, w: bw + 4, h: height + 8 })
    })

    if (overflow > 0) {
      ctx.textAlign = 'right'
      ctx.font = '11px "PingFang SC", sans-serif'
      ctx.fillStyle = 'rgba(15, 43, 70, 0.45)'
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
      if (view.value === 'water') renderChart()
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
  background: linear-gradient(180deg, #F5FAFF 0%, #EDF6FF 100%);
  color: #0F2B46;
  border-radius: 16px;
}
.top { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; flex-wrap: wrap; }
.title { font-size: 24px; font-weight: 700; letter-spacing: 0.02em; color: #0F2B46; }
.subtitle { margin-top: 4px; font-size: 12.5px; color: #5B7083; }
.kpis { display: flex; gap: 26px; }
.kpi-value { font-size: 26px; font-weight: 700; color: #0A84FF; font-variant-numeric: tabular-nums; }
.kpi-label { font-size: 12px; color: #5B7083; margin-top: 2px; }
.tools { display: flex; align-items: center; gap: 12px; }
.switch { display: inline-flex; background: #FFFFFF; border: 1px solid #DCEBFA; border-radius: 10px; padding: 3px; box-shadow: 0 2px 8px rgba(10, 132, 255, 0.06); }
.switch button { background: transparent; border: 0; color: #5B7083; padding: 6px 14px; font-size: 12.5px; border-radius: 8px; cursor: pointer; }
.switch button.active { background: linear-gradient(135deg, #EAF5FF, #D6EBFF); color: #0A84FF; font-weight: 600; }
.search { width: 240px; background: #FFFFFF; border: 1px solid #DCEBFA; border-radius: 10px; padding: 8px 12px; color: #0F2B46; outline: none; font-size: 12.5px; }
.search::placeholder { color: #93A8BC; }
.stage-wrap { display: flex; gap: 16px; margin-top: 16px; align-items: stretch; }
.stage { position: relative; flex: 1; min-width: 0; height: calc(100vh - 230px); min-height: 480px; background: #FFFFFF; border: 1px solid #DCEBFA; border-radius: 16px; overflow: hidden; box-shadow: 0 6px 24px rgba(10, 132, 255, 0.08); }
.water-bg { position: absolute; inset: 0; }
.veil { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(255,255,255,0.42), rgba(255,255,255,0.56)); pointer-events: none; }
.chart, .city { width: 100%; height: 100%; display: block; position: relative; z-index: 2; }
.river-legend { position: absolute; left: 18px; bottom: 14px; display: flex; align-items: center; gap: 8px; font-size: 11.5px; color: #5B7083; background: rgba(255,255,255,0.75); padding: 6px 12px; border-radius: 999px; border: 1px solid #E1EEF9; }
.river-legend i { width: 22px; height: 2px; background: linear-gradient(90deg, rgba(10,132,255,0.15), rgba(10,132,255,0.55)); border-radius: 2px; display: inline-block; }
.focus-chip { position: absolute; top: 14px; left: 16px; background: #FFFFFF; border: 1px solid #DCEBFA; padding: 6px 12px; border-radius: 999px; font-size: 12.5px; color: #0F2B46; box-shadow: 0 2px 8px rgba(10, 132, 255, 0.08); }
.focus-chip button { margin-left: 10px; background: transparent; border: 0; color: #0A84FF; cursor: pointer; font-size: 12.5px; }
.empty-tip { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #8FA8BC; font-size: 13px; }
.detail { width: 300px; flex-shrink: 0; background: #FFFFFF; border: 1px solid #DCEBFA; border-radius: 16px; padding: 18px; position: relative; box-shadow: 0 6px 24px rgba(10, 132, 255, 0.08); }
.detail-close { position: absolute; right: 14px; top: 10px; color: #93A8BC; cursor: pointer; font-size: 18px; }
.detail-domain { font-size: 12px; color: #0A84FF; }
.detail-name { margin-top: 6px; font-size: 18px; font-weight: 700; line-height: 1.4; color: #0F2B46; }
.detail-code { margin-top: 4px; font-size: 11.5px; color: #5B7083; word-break: break-all; }
.detail-grid { margin-top: 16px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.detail-grid div { font-size: 13px; color: #0F2B46; }
.detail-grid span { display: block; font-size: 11.5px; color: #5B7083; margin-bottom: 2px; }
.detail-actions { margin-top: 20px; display: flex; flex-direction: column; gap: 8px; }
.detail-actions button { background: #F5FAFF; border: 1px solid #DCEBFA; color: #0F2B46; padding: 9px 12px; border-radius: 10px; cursor: pointer; font-size: 13px; }
.detail-actions button.primary { background: linear-gradient(135deg, #5AC8FA, #0A84FF); border-color: transparent; color: #FFFFFF; font-weight: 600; }
.legend { margin-top: 14px; display: flex; flex-wrap: wrap; gap: 8px; padding-bottom: 4px; }
.legend-item { display: inline-flex; align-items: center; gap: 7px; background: #FFFFFF; border: 1px solid #E1EEF9; color: #0F2B46; border-radius: 999px; padding: 5px 12px; font-size: 12px; cursor: pointer; }
.legend-item i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.legend-item em { font-style: normal; color: #5B7083; }
.legend-item.dim { opacity: 0.35; }
</style>
