<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand">
        <img v-if="brand.logo" :src="brand.logo" class="brand-logo" alt="logo" />
        <span v-else class="drop"></span>
        <span class="brand-text">{{ brand.name || '水务指标平台' }}</span>
      </div>
      <div class="subtitle">{{ brand.subtitle || '登录后进入指标管理' }}</div>
      <el-form @submit.prevent="onSubmit">
        <el-form-item>
          <el-input v-model="username" placeholder="用户名" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="submit-btn"
          :loading="loading"
          @click="onSubmit"
        >
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useBrandStore } from '@/stores/brand'

const router = useRouter()
const authStore = useAuthStore()
const brand = useBrandStore()
const username = ref('')
const password = ref('')
const loading = ref(false)

onMounted(() => {
  brand.load()
})

async function onSubmit() {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await authStore.login(username.value, password.value)
    ElMessage.success('登录成功')
    router.push('/')
  } catch {
    // 错误提示已由 http 拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.brand-logo {
  width: 36px;
  height: 36px;
  object-fit: contain;
  border-radius: 10px;
}
.login-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #edf6ff 0%, #f7fbff 40%, #eaf4ff 100%);
}
.login-card {
  width: 360px;
  padding: 40px 36px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  box-shadow: 0 8px 30px rgba(10, 132, 255, 0.08);
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.drop {
  width: 18px;
  height: 18px;
  border-radius: 50% 50% 50% 0;
  background: var(--gradient-primary);
  transform: rotate(-45deg);
}
.brand-text {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text);
}
.subtitle {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 24px;
}
.submit-btn {
  width: 100%;
  background: var(--gradient-primary);
  border: none;
}
</style>
