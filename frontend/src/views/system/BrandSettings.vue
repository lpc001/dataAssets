<template>
  <div class="page">
    <div class="page-head">
      <div>
        <div class="page-title">品牌设置</div>
        <div class="page-sub">定制系统名称与 Logo，侧栏和登录页都会同步</div>
      </div>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-card shadow="never" class="block">
      <template #header>预览</template>
      <div class="preview">
        <img v-if="form.logo" :src="form.logo" class="preview-logo" alt="logo" />
        <span v-else class="drop" />
        <span class="preview-name">
          <span>{{ partsOf(form.name).head }}</span><b>{{ partsOf(form.name).tail }}</b>
        </span>
        <span v-if="form.subtitle" class="preview-sub">{{ form.subtitle }}</span>
      </div>
    </el-card>

    <el-card shadow="never" class="block">
      <template #header>配置</template>
      <el-form label-width="100px" @submit.prevent>
        <el-form-item label="系统名称">
          <el-input v-model="form.name" maxlength="64" show-word-limit placeholder="如 银河联邦水务·指标平台" />
        </el-form-item>
        <el-form-item label="副标题">
          <el-input v-model="form.subtitle" maxlength="128" placeholder="登录页副标题，可留空" />
        </el-form-item>
        <el-form-item label="Logo">
          <div class="logo-row">
            <img v-if="form.logo" :src="form.logo" class="logo-thumb" alt="logo" />
            <span v-else class="drop" />
            <input ref="fileInput" type="file" accept="image/*" class="file-input" @change="onFile" />
            <el-button @click="pickFile">上传图片</el-button>
            <el-button v-if="form.logo" @click="form.logo = ''">清除（用默认）</el-button>
          </div>
          <div class="hint">建议 200×200 以内的 PNG / SVG，500KB 以内；存入数据库，无需额外静态目录</div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
          <el-button :loading="resetting" @click="onReset">恢复默认</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getBrand, resetBrand, updateBrand } from '@/api/brand'
import { useBrandStore } from '@/stores/brand'

const brand = useBrandStore()
const form = reactive({ name: '', subtitle: '', logo: '' })
const saving = ref(false)
const resetting = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const MAX_BYTES = 500 * 1024

function partsOf(name: string) {
  const text = name || '水投·指标平台'
  const idx = text.indexOf('·')
  if (idx < 0) return { head: text, tail: '' }
  return { head: text.slice(0, idx + 1), tail: text.slice(idx + 1) }
}

async function load() {
  const info = await getBrand()
  form.name = info.name
  form.subtitle = info.subtitle
  form.logo = info.logo
}

function pickFile() {
  fileInput.value?.click()
}

function onFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件')
    return
  }
  if (file.size > MAX_BYTES) {
    ElMessage.warning('图片超过 500KB，请压缩后再上传')
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    form.logo = String(reader.result || '')
  }
  reader.readAsDataURL(file)
  input.value = ''
}

async function onSave() {
  if (!form.name.trim()) {
    ElMessage.warning('系统名称不能为空')
    return
  }
  saving.value = true
  try {
    const info = await updateBrand({ name: form.name.trim(), subtitle: form.subtitle, logo: form.logo })
    form.name = info.name
    form.subtitle = info.subtitle
    form.logo = info.logo
    await brand.load(true)
    ElMessage.success('已保存，侧栏与登录页立即生效')
  } finally {
    saving.value = false
  }
}

async function onReset() {
  await ElMessageBox.confirm('恢复为系统默认品牌（水投·指标平台）？', '提示', { type: 'warning' })
  resetting.value = true
  try {
    const info = await resetBrand()
    form.name = info.name
    form.subtitle = info.subtitle
    form.logo = info.logo
    await brand.load(true)
    ElMessage.success('已恢复默认')
  } finally {
    resetting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page {
  padding: 20px;
}
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}
.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2d3d;
}
.page-sub {
  font-size: 13px;
  color: #6b8299;
  margin-top: 4px;
}
.block {
  margin-bottom: 16px;
}
.preview {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.preview-logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
  border-radius: 10px;
}
.preview-name {
  font-size: 20px;
  color: #1f2d3d;
}
.preview-name b {
  color: #0a84ff;
}
.preview-sub {
  font-size: 13px;
  color: #6b8299;
}
.logo-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.logo-thumb {
  width: 44px;
  height: 44px;
  object-fit: contain;
  border: 1px solid #e6ecf3;
  border-radius: 10px;
  background: #fff;
}
.file-input {
  display: none;
}
.drop {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #4fc3f7, #0d47a1);
  display: inline-block;
}
.hint {
  font-size: 12px;
  color: #8a9bb0;
  margin-top: 4px;
}
</style>
