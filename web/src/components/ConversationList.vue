<script setup lang="ts">
import type { Conversation } from '../types/api'
defineProps<{ conversations: Conversation[] }>()
</script>

<template>
  <div v-if="conversations.length" class="list">
    <RouterLink v-for="item in conversations" :key="item.id" class="card list-item" :to="`/conversations/${item.id}`">
      <div><h3>{{ item.name }}</h3><small>{{ new Date(item.updated_at).toLocaleString() }}</small></div>
      <span>进入 →</span>
    </RouterLink>
  </div>
  <div v-else class="empty">还没有会话，创建第一个会话吧。</div>
</template>
