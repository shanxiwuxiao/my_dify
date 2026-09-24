<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getApp } from '../api/apps'
import { createConversation, listConversations } from '../api/conversations'
import ConversationList from '../components/ConversationList.vue'
import type { App, Conversation } from '../types/api'

const route = useRoute(); const router = useRouter(); const appId = String(route.params.appId)
const app = ref<App>(); const conversations = ref<Conversation[]>([]); const name = ref('新会话'); const error = ref(''); const submitting = ref(false)
async function load() {
  try { [app.value, conversations.value] = await Promise.all([getApp(appId), listConversations(appId).then(value => value.items)]) }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '加载失败' }
}
async function create() {
  if (!name.value.trim()) return
  submitting.value = true; error.value = ''
  try { const item = await createConversation(appId, name.value.trim()); await router.push(`/conversations/${item.id}`) }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '创建失败' }
  finally { submitting.value = false }
}
onMounted(load)
</script>

<template>
  <RouterLink class="back" to="/apps">← 返回应用</RouterLink>
  <section v-if="app" class="page-heading"><div><h1>{{ app.name }}</h1><p>{{ app.description || '暂无描述' }}</p></div><span class="badge">{{ app.model_name }}</span></section>
  <p v-if="error" class="error-banner">{{ error }}</p>
  <section class="card create-conversation"><div><h2>开始新会话</h2><p>历史消息会保存在本地数据库中。</p></div><form @submit.prevent="create"><input v-model="name" maxlength="100"><button class="primary" :disabled="submitting">创建并进入</button></form></section>
  <section class="section"><h2>历史会话</h2><ConversationList :conversations="conversations" /></section>
</template>
