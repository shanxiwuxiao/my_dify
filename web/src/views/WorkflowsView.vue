<script setup lang="ts">
import { onMounted,ref } from 'vue'
import { createWorkflow,deleteWorkflow,listWorkflows,runWorkflow,updateWorkflow } from '../api/workflows'
import type { Workflow,WorkflowRun } from '../types/api'
const sample={nodes:[{id:'start',type:'start'},{id:'template',type:'template',config:{template:'你好，{{name}}',output_key:'result'}},{id:'end',type:'end',config:{output:'result'}}],edges:[{source:'start',target:'template'},{source:'template',target:'end'}]}
const workflows=ref<Workflow[]>([]),selected=ref<Workflow>(),name=ref('欢迎工作流'),definition=ref(JSON.stringify(sample,null,2)),inputs=ref('{"name":"小明"}'),run=ref<WorkflowRun>(),error=ref('')
async function load(){workflows.value=(await listWorkflows()).items}
function choose(item:Workflow){selected.value=item;name.value=item.name;definition.value=JSON.stringify(item.definition,null,2);run.value=undefined}
async function save(){try{const graph=JSON.parse(definition.value);const item=selected.value?await updateWorkflow(selected.value.id,name.value,graph):await createWorkflow(name.value,graph);if(!selected.value)workflows.value.unshift(item);else workflows.value[workflows.value.findIndex(x=>x.id===item.id)]=item;choose(item)}catch(e){error.value=e instanceof Error?e.message:'保存失败'}}
async function execute(){if(!selected.value)return;try{run.value=await runWorkflow(selected.value.id,JSON.parse(inputs.value))}catch(e){error.value=e instanceof Error?e.message:'运行失败'}}
async function remove(item:Workflow){if(!confirm(`删除“${item.name}”？`))return;await deleteWorkflow(item.id);workflows.value=workflows.value.filter(x=>x.id!==item.id);if(selected.value?.id===item.id)selected.value=undefined}
function fresh(){selected.value=undefined;name.value='新工作流';definition.value=JSON.stringify(sample,null,2);run.value=undefined}
onMounted(load)
</script>
<template><section class="page-heading"><div><h1>工作流</h1><p>用 DAG 编排模板、条件、知识检索与 LLM 节点。</p></div><button @click="fresh">新建</button></section><p v-if="error" class="error-banner">{{error}}</p><div class="workflow-layout"><aside class="list"><article v-for="item in workflows" :key="item.id" class="card list-item"><button class="conversation-link" @click="choose(item)">{{item.name}}</button><button class="danger" @click="remove(item)">删除</button></article></aside><main><form class="card form-grid" @submit.prevent="save"><label>名称<input v-model="name" required></label><label>工作流定义<textarea v-model="definition" rows="20" class="code-editor" required /></label><button class="primary">{{selected?'保存':'创建'}}</button></form><section v-if="selected" class="card form-grid section"><h2>运行调试</h2><label>输入 JSON<textarea v-model="inputs" rows="4" class="code-editor" /></label><button type="button" class="primary" @click="execute">运行</button><pre v-if="run">{{JSON.stringify(run,null,2)}}</pre></section></main></div></template>
