<script setup lang="ts">
import { reactive } from 'vue'
import type { CreateAppInput } from '../types/api'

const props = defineProps<{ submitting: boolean }>()
const emit = defineEmits<{ submit: [value: CreateAppInput] }>()
const form = reactive<CreateAppInput>({ name: '', description: '', system_prompt: '你是一个乐于助人的 AI 助手。', model_name: 'deepseek-chat', temperature: 0.7 })

function submit() {
  if (!form.name.trim() || props.submitting) return
  emit('submit', { ...form, name: form.name.trim() })
}
</script>

<template>
  <form class="card form-grid" @submit.prevent="submit">
    <h2>创建应用</h2>
    <label>名称<input v-model="form.name" required maxlength="100" placeholder="例如：学习助手"></label>
    <label>描述<input v-model="form.description" maxlength="500" placeholder="这个应用能做什么？"></label>
    <label>系统提示词<textarea v-model="form.system_prompt" rows="4" maxlength="10000" /></label>
    <div class="form-row">
      <label>模型<input v-model="form.model_name" required></label>
      <label>Temperature<input v-model.number="form.temperature" type="number" min="0" max="2" step="0.1"></label>
    </div>
    <button class="primary" :disabled="submitting">{{ submitting ? '创建中…' : '创建应用' }}</button>
  </form>
</template>
