<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
const auth = useAuthStore(); const router = useRouter()
async function signOut() { await auth.logout(); await router.push('/auth') }
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink class="brand" to="/apps">my_dify</RouterLink>
      <span class="subtitle">用自己的代码理解 LLM 应用</span>
      <RouterLink v-if="auth.user" to="/model-providers">模型供应商</RouterLink>
      <RouterLink v-if="auth.user" to="/knowledge">知识库</RouterLink>
      <RouterLink v-if="auth.user" to="/workflows">工作流</RouterLink>
      <RouterLink v-if="auth.user" to="/observability">评测监控</RouterLink>
      <div v-if="auth.user" class="account"><span>{{ auth.user.email }}</span><button @click="signOut">退出</button></div>
    </header>
    <main class="page-container"><RouterView /></main>
  </div>
</template>
