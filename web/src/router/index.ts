import { createRouter, createWebHistory } from 'vue-router'
import AppListView from '../views/AppListView.vue'
import AppDetailView from '../views/AppDetailView.vue'
import ConversationView from '../views/ConversationView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/apps' },
    { path: '/apps', component: AppListView },
    { path: '/apps/:appId', component: AppDetailView },
    { path: '/conversations/:id', component: ConversationView },
  ],
})
