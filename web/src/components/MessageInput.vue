<script setup lang="ts">
import { ref } from 'vue'
defineProps<{ streaming: boolean }>()
const emit = defineEmits<{ send: [message: string]; stop: [] }>()
const text = ref('')
function send() {
  const message = text.value.trim()
  if (!message) return
  emit('send', message)
  text.value = ''
}
</script>

<template>
  <form class="composer" @submit.prevent="send">
    <textarea v-model="text" rows="2" :disabled="streaming" placeholder="输入消息，Enter 发送，Shift + Enter 换行" @keydown.enter.exact.prevent="send" />
    <button v-if="streaming" type="button" class="danger" @click="emit('stop')">停止生成</button>
    <button v-else class="primary" :disabled="!text.trim()">发送</button>
  </form>
</template>
