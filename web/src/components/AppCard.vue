<script setup lang="ts">
import type { App } from '../types/api'
defineProps<{ app: App }>()
</script>

<template>
  <RouterLink class="card app-card" :to="`/apps/${app.id}`">
    <div class="card-icon">AI</div>
    <div>
      <h3>{{ app.name }}</h3>
      <p>{{ app.description || '暂无描述' }}</p>
      <small>{{ app.model_name }} · temperature {{ app.temperature }}</small>
    </div>
  </RouterLink>
</template>
