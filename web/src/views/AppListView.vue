<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { createApp, listApps } from '../api/apps'
import AppCard from '../components/AppCard.vue'
import AppCreateForm from '../components/AppCreateForm.vue'
import type { App, CreateAppInput } from '../types/api'

const apps = ref<App[]>([])
const loading = ref(true)
const submitting = ref(false)
const error = ref('')
async function load() {
  try { apps.value = (await listApps()).items }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '加载失败' }
  finally { loading.value = false }
}
async function submit(input: CreateAppInput) {
  submitting.value = true; error.value = ''
  try { apps.value.unshift(await createApp(input)) }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '创建失败' }
  finally { submitting.value = false }
}
onMounted(load)
</script>

<template>
  <section class="page-heading"><div><h1>应用</h1><p>创建一个带独立提示词和模型参数的 AI 应用。</p></div></section>
  <p v-if="error" class="error-banner">{{ error }}</p>
  <div class="two-columns">
    <AppCreateForm :submitting="submitting" @submit="submit" />
    <section><h2>我的应用</h2><p v-if="loading" class="empty">加载中…</p><div v-else-if="apps.length" class="app-grid"><AppCard v-for="app in apps" :key="app.id" :app="app" /></div><div v-else class="empty">还没有应用。</div></section>
  </div>
</template>
