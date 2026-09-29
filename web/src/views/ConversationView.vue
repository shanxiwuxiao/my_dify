<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getConversation, getMessages } from '../api/conversations'
import { streamConversationMessage } from '../api/stream'
import MessageInput from '../components/MessageInput.vue'
import MessageList from '../components/MessageList.vue'
import type { Conversation, KnowledgeSource, Message } from '../types/api'

const id = String(useRoute().params.id)
const conversation = ref<Conversation>(); const messages = ref<Message[]>([]); const streaming = ref(false); const error = ref(''); let controller: AbortController | undefined
const sources = ref<KnowledgeSource[]>([])
async function refreshMessages() { messages.value = (await getMessages(id)).items }
async function load() {
  try { [conversation.value] = await Promise.all([getConversation(id), refreshMessages()]) }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '加载失败' }
}
async function send(content: string) {
  if (streaming.value) return
  error.value = ''; streaming.value = true; controller = new AbortController()
  sources.value = []
  const now = new Date().toISOString()
  messages.value.push({ id: `user-${Date.now()}`, conversation_id: id, role: 'user', content, status: 'completed', created_at: now })
  const assistant: Message = { id: `assistant-${Date.now()}`, conversation_id: id, role: 'assistant', content: '', status: 'streaming', created_at: now }
  messages.value.push(assistant)
  const assistantIndex = messages.value.length - 1
  try {
    await streamConversationMessage(id, content, {
      onMessage: delta => { messages.value[assistantIndex]!.content += delta },
      onDone: () => { messages.value[assistantIndex]!.status = 'completed' },
      onError: message => { throw new Error(message) },
      onSources: items => { sources.value = items },
    }, controller.signal)
  } catch (reason) {
    if (!(reason instanceof DOMException && reason.name === 'AbortError')) error.value = reason instanceof Error ? reason.message : '发送失败'
  } finally {
    streaming.value = false; controller = undefined
    try { await refreshMessages() } catch { error.value ||= '刷新消息失败' }
  }
}
function stop() { controller?.abort() }
onMounted(load); onBeforeUnmount(stop)
</script>

<template>
  <div class="chat-page">
    <header class="chat-heading"><RouterLink v-if="conversation" class="back" :to="`/apps/${conversation.app_id}`">← 返回会话列表</RouterLink><h1>{{ conversation?.name ?? '会话' }}</h1><p v-if="error" class="error-banner">{{ error }}</p></header>
    <MessageList :messages="messages" />
    <details v-if="sources.length" class="sources"><summary>参考资料（{{ sources.length }}）</summary><p v-for="item in sources" :key="item.segment_id"><strong>{{ item.document_name }}</strong>：{{ item.content }}</p></details>
    <MessageInput :streaming="streaming" @send="send" @stop="stop" />
  </div>
</template>
