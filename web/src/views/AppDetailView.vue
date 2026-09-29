<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { debugApp, deleteApp, getApp, listAppVersions, publishApp, updateApp } from '../api/apps'
import { createConversation, deleteConversation, listConversations, renameConversation } from '../api/conversations'
import { listModelProviders } from '../api/modelProviders'
import { bindAppKnowledge, getAppKnowledge, listKnowledgeBases } from '../api/knowledge'
import { runAgent } from '../api/agent'
import ConversationList from '../components/ConversationList.vue'
import type { App, AppVersion, Conversation, KnowledgeBase, ModelProvider, UpdateAppInput } from '../types/api'

const route = useRoute()
const router = useRouter()
const appId = String(route.params.appId)
const app = ref<App>()
const conversations = ref<Conversation[]>([])
const name = ref('新会话')
const error = ref('')
const success = ref('')
const submitting = ref(false)
const saving = ref(false)
const deletingApp = ref(false)
const publishing = ref(false)
const versions = ref<AppVersion[]>([])
const providers = ref<ModelProvider[]>([])
const knowledgeBases = ref<KnowledgeBase[]>([])
const selectedKnowledge = ref<string[]>([])
const debugMessage = ref('')
const debugAnswer = ref('')
const debugging = ref(false)
const agentQuery = ref('')
const agentResult = ref<Awaited<ReturnType<typeof runAgent>>>()
const agentRunning = ref(false)
const form = reactive<UpdateAppInput>({
  name: '', description: '', system_prompt: '', model_name: '', temperature: 0.7, provider_id: null,
})

function fillForm(value: App) {
  Object.assign(form, {
    name: value.name,
    description: value.description,
    system_prompt: value.system_prompt,
    model_name: value.model_name,
    temperature: value.temperature,
    provider_id: value.provider_id,
  })
}

async function load() {
  error.value = ''
  try {
    const [appValue, conversationValue, versionValue, providerValue, knowledgeValue, boundValue] = await Promise.all([
      getApp(appId),
      listConversations(appId),
      listAppVersions(appId),
      listModelProviders(),
      listKnowledgeBases(),
      getAppKnowledge(appId),
    ])
    app.value = appValue
    conversations.value = conversationValue.items
    versions.value = versionValue.items
    providers.value = providerValue.items
    knowledgeBases.value = knowledgeValue.items
    selectedKnowledge.value = boundValue.knowledge_base_ids
    fillForm(appValue)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '加载失败'
  }
}

async function saveKnowledge() {
  try { await bindAppKnowledge(appId, selectedKnowledge.value); success.value = '知识库绑定已保存' }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '保存失败' }
}

async function debugPrompt() {
  if (!debugMessage.value.trim()) return
  debugging.value = true; error.value = ''; debugAnswer.value = ''
  try { debugAnswer.value = (await debugApp(appId, debugMessage.value.trim())).answer }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '调试失败' }
  finally { debugging.value = false }
}

async function executeAgent() {
  if (!agentQuery.value.trim()) return
  agentRunning.value = true; error.value = ''; agentResult.value = undefined
  try { agentResult.value = await runAgent(appId, agentQuery.value.trim()) }
  catch (reason) { error.value = reason instanceof Error ? reason.message : 'Agent 运行失败' }
  finally { agentRunning.value = false }
}

async function publish() {
  publishing.value = true; error.value = ''; success.value = ''
  try {
    const version = await publishApp(appId)
    versions.value.unshift(version)
    if (app.value) app.value.published_version = version.version
    success.value = `版本 v${version.version} 已发布`
  } catch (reason) { error.value = reason instanceof Error ? reason.message : '发布失败' }
  finally { publishing.value = false }
}

async function create() {
  if (!name.value.trim()) return
  submitting.value = true
  error.value = ''
  try {
    const item = await createConversation(appId, name.value.trim())
    await router.push(`/conversations/${item.id}`)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '创建失败'
  } finally {
    submitting.value = false
  }
}

async function saveApp() {
  if (!form.name.trim() || !form.model_name.trim()) return
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    app.value = await updateApp(appId, { ...form })
    fillForm(app.value)
    success.value = '应用设置已保存'
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '保存失败'
  } finally {
    saving.value = false
  }
}

async function removeApp() {
  if (!window.confirm('删除应用后，它的会话和消息也会被删除。确定继续吗？')) return
  deletingApp.value = true
  error.value = ''
  try {
    await deleteApp(appId)
    await router.push('/apps')
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '删除失败'
    deletingApp.value = false
  }
}

async function rename(item: Conversation, newName: string) {
  error.value = ''
  try {
    const updated = await renameConversation(item.id, newName)
    const index = conversations.value.findIndex(value => value.id === updated.id)
    if (index >= 0) conversations.value[index] = updated
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '重命名失败'
  }
}

async function removeConversation(item: Conversation) {
  if (!window.confirm(`确定删除会话“${item.name}”吗？`)) return
  error.value = ''
  try {
    await deleteConversation(item.id)
    conversations.value = conversations.value.filter(value => value.id !== item.id)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '删除失败'
  }
}

onMounted(load)
</script>

<template>
  <RouterLink class="back" to="/apps">← 返回应用</RouterLink>
  <section v-if="app" class="page-heading">
    <div><h1>{{ app.name }}</h1><p>{{ app.description || '暂无描述' }}</p></div>
    <span class="badge">{{ app.model_name }}</span>
  </section>
  <p v-if="error" class="error-banner">{{ error }}</p>
  <p v-if="success" class="success-banner">{{ success }}</p>

  <div v-if="app" class="detail-grid">
    <form class="card form-grid" @submit.prevent="saveApp">
      <h2>应用设置</h2>
      <label>名称<input v-model="form.name" required maxlength="100"></label>
      <label>描述<input v-model="form.description" maxlength="500"></label>
      <label>系统提示词<textarea v-model="form.system_prompt" rows="5" maxlength="10000" /></label>
      <label>模型供应商<select v-model="form.provider_id"><option :value="null">环境变量默认供应商</option><option v-for="item in providers" :key="item.id" :value="item.id">{{ item.name }}</option></select></label>
      <div class="form-row">
        <label>模型<input v-model="form.model_name" required maxlength="100"></label>
        <label>Temperature<input v-model.number="form.temperature" type="number" min="0" max="2" step="0.1"></label>
      </div>
      <button class="primary" :disabled="saving">{{ saving ? '保存中…' : '保存设置' }}</button>
      <button type="button" :disabled="publishing" @click="publish">{{ publishing ? '发布中…' : '发布当前配置' }}</button>
      <small>线上版本：{{ app.published_version ? `v${app.published_version}` : '尚未发布（暂用草稿）' }}</small>
      <details v-if="versions.length"><summary>历史版本（{{ versions.length }}）</summary><ol><li v-for="version in versions" :key="version.id">v{{ version.version }} · {{ version.model_name }} · {{ new Date(version.created_at).toLocaleString() }}</li></ol></details>
      <fieldset><legend>关联知识库</legend><label v-for="item in knowledgeBases" :key="item.id" class="check-row"><input v-model="selectedKnowledge" type="checkbox" :value="item.id">{{ item.name }}</label><button type="button" @click="saveKnowledge">保存知识库绑定</button></fieldset>
    </form>

    <div>
      <section class="card form-grid">
        <h2>草稿 Prompt 调试</h2>
        <p>这里始终使用左侧当前保存的草稿，不影响已发布版本。</p>
        <textarea v-model="debugMessage" rows="3" placeholder="输入测试问题" />
        <button class="primary" :disabled="debugging" @click="debugPrompt">{{ debugging ? '生成中…' : '运行调试' }}</button>
        <div v-if="debugAnswer" class="message-content">{{ debugAnswer }}</div>
      </section>
      <section class="card create-conversation">
        <div><h2>开始新会话</h2><p>历史消息会保存在数据库中。</p></div>
        <form @submit.prevent="create"><input v-model="name" maxlength="100"><button class="primary" :disabled="submitting">创建并进入</button></form>
      </section>
      <section class="card form-grid section">
        <h2>Agent 调试</h2>
        <textarea v-model="agentQuery" rows="3" placeholder="输入需要工具协助完成的任务" />
        <button class="primary" :disabled="agentRunning" @click="executeAgent">{{ agentRunning ? '执行中…' : '运行 Agent' }}</button>
        <div v-if="agentResult"><div class="message-content">{{ agentResult.answer }}</div><details v-if="agentResult.trace.length"><summary>工具轨迹（{{ agentResult.trace.length }}）</summary><pre>{{ JSON.stringify(agentResult.trace, null, 2) }}</pre></details></div>
      </section>
      <section class="section"><h2>历史会话</h2><ConversationList :conversations="conversations" @rename="rename" @delete="removeConversation" /></section>
    </div>
  </div>

  <section v-if="app" class="card danger-zone">
    <div><h2>危险操作</h2><p>永久删除应用及其全部会话和消息。</p></div>
    <button class="danger" :disabled="deletingApp" @click="removeApp">{{ deletingApp ? '删除中…' : '删除应用' }}</button>
  </section>
</template>
