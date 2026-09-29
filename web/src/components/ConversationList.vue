<script setup lang="ts">
import { ref } from 'vue'
import type { Conversation } from '../types/api'

defineProps<{ conversations: Conversation[] }>()
const emit = defineEmits<{
  rename: [conversation: Conversation, name: string]
  delete: [conversation: Conversation]
}>()
const editingId = ref('')
const editingName = ref('')

function beginEditing(item: Conversation) {
  editingId.value = item.id
  editingName.value = item.name
}

function save(item: Conversation) {
  const name = editingName.value.trim()
  if (!name) return
  emit('rename', item, name)
  editingId.value = ''
}
</script>

<template>
  <div v-if="conversations.length" class="list">
    <article v-for="item in conversations" :key="item.id" class="card list-item">
      <form v-if="editingId === item.id" class="inline-edit" @submit.prevent="save(item)">
        <input v-model="editingName" maxlength="100" autofocus>
        <button class="primary">保存</button>
        <button type="button" @click="editingId = ''">取消</button>
      </form>
      <template v-else>
        <RouterLink class="conversation-link" :to="`/conversations/${item.id}`">
          <div><h3>{{ item.name }}</h3><small>{{ new Date(item.updated_at).toLocaleString() }}</small></div>
          <span>进入 →</span>
        </RouterLink>
        <div class="item-actions">
          <button type="button" @click="beginEditing(item)">重命名</button>
          <button type="button" class="danger" @click="emit('delete', item)">删除</button>
        </div>
      </template>
    </article>
  </div>
  <div v-else class="empty">还没有会话，创建第一个会话吧。</div>
</template>
