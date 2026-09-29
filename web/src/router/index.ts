import { createRouter, createWebHistory } from 'vue-router'
import AppListView from '../views/AppListView.vue'
import AppDetailView from '../views/AppDetailView.vue'
import ConversationView from '../views/ConversationView.vue'
import AuthView from '../views/AuthView.vue'
import ModelProvidersView from '../views/ModelProvidersView.vue'
import KnowledgeView from '../views/KnowledgeView.vue'
import WorkflowsView from '../views/WorkflowsView.vue'
import ObservabilityView from '../views/ObservabilityView.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/apps' },
    { path: '/auth', component: AuthView, meta: { public: true } },
    { path: '/apps', component: AppListView },
    { path: '/model-providers', component: ModelProvidersView },
    { path: '/knowledge', component: KnowledgeView },
    { path: '/workflows', component: WorkflowsView },
    { path: '/observability', component: ObservabilityView },
    { path: '/apps/:appId', component: AppDetailView },
    { path: '/conversations/:id', component: ConversationView },
  ],
})

router.beforeEach(async to => {
  const auth = useAuthStore()
  await auth.restore()
  if (!to.meta.public && !auth.user) return { path: '/auth', query: { redirect: to.fullPath } }
  if (to.path === '/auth' && auth.user) return '/apps'
})

export default router
