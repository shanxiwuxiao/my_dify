<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import type { Message } from '../types/api'
const props = defineProps<{ messages: Message[] }>()
const container = ref<HTMLElement>()
watch(() => props.messages.map(item => item.content).join(''), async () => {
  await nextTick()
  container.value?.scrollTo({ top: container.value.scrollHeight, behavior: 'smooth' })
})
</script>

<template>
  <div ref="container" class="messages">
    <div v-if="!messages.length" class="empty">发送一条消息，开始你们的对话。</div>
    <article v-for="message in messages" :key="message.id" class="message" :class="message.role">
      <strong>{{ message.role === 'user' ? '你' : 'AI' }}</strong>
      <div class="message-content">{{ message.content || '思考中…' }}</div>
    </article>
  </div>
</template>
