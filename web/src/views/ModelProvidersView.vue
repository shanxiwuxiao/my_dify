<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { createModelProvider, deleteModelProvider, listModelProviders } from '../api/modelProviders'
import type { ModelProvider } from '../types/api'
const providers = ref<ModelProvider[]>([]); const error = ref(''); const busy = ref(false)
const form = reactive({ name: 'DeepSeek', base_url: 'https://api.deepseek.com/v1', api_key: '', default_model: 'deepseek-chat' })
async function load() { try { providers.value = (await listModelProviders()).items } catch (e) { error.value = e instanceof Error ? e.message : '加载失败' } }
async function create() { busy.value = true; error.value = ''; try { providers.value.unshift(await createModelProvider({ ...form })); form.api_key = '' } catch (e) { error.value = e instanceof Error ? e.message : '创建失败' } finally { busy.value = false } }
async function remove(item: ModelProvider) { if (!confirm(`删除供应商“${item.name}”？`)) return; try { await deleteModelProvider(item.id); providers.value = providers.value.filter(p => p.id !== item.id) } catch (e) { error.value = e instanceof Error ? e.message : '删除失败' } }
onMounted(load)
</script>
<template><section class="page-heading"><div><h1>模型供应商</h1><p>密钥加密保存在服务端，永远不会返回浏览器。</p></div></section><p v-if="error" class="error-banner">{{ error }}</p><div class="two-columns"><form class="card form-grid" @submit.prevent="create"><h2>添加 OpenAI 兼容供应商</h2><label>名称<input v-model="form.name" required></label><label>Base URL<input v-model="form.base_url" type="url" required></label><label>默认模型<input v-model="form.default_model" required></label><label>API Key<input v-model="form.api_key" type="password" required></label><button class="primary" :disabled="busy">添加供应商</button></form><section><h2>已配置</h2><div class="list"><article v-for="item in providers" :key="item.id" class="card list-item"><div><h3>{{ item.name }}</h3><small>{{ item.default_model }} · {{ item.api_key_masked }}</small></div><button class="danger" @click="remove(item)">删除</button></article></div></section></div></template>
