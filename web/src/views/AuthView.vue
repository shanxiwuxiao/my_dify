<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore(); const route = useRoute(); const router = useRouter()
const email = ref(''); const password = ref(''); const mode = ref<'login' | 'register'>('login'); const busy = ref(false); const error = ref('')
async function submit() {
  busy.value = true; error.value = ''
  try {
    if (mode.value === 'login') await auth.login(email.value, password.value)
    else await auth.register(email.value, password.value)
    await router.replace(typeof route.query.redirect === 'string' ? route.query.redirect : '/apps')
  } catch (reason) { error.value = reason instanceof Error ? reason.message : '认证失败' }
  finally { busy.value = false }
}
</script>

<template>
  <div class="auth-wrap"><form class="card form-grid auth-card" @submit.prevent="submit">
    <h1>{{ mode === 'login' ? '登录 my_dify' : '创建账号' }}</h1>
    <p>你的应用、会话和知识数据只属于当前账号。</p>
    <p v-if="error" class="error-banner">{{ error }}</p>
    <label>邮箱<input v-model="email" type="email" required autocomplete="email"></label>
    <label>密码<input v-model="password" type="password" required minlength="8" autocomplete="current-password"></label>
    <button class="primary" :disabled="busy">{{ busy ? '处理中…' : mode === 'login' ? '登录' : '注册' }}</button>
    <button type="button" @click="mode = mode === 'login' ? 'register' : 'login'">{{ mode === 'login' ? '没有账号？注册' : '已有账号？登录' }}</button>
  </form></div>
</template>
