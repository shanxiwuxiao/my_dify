import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as authApi from '../api/auth'
import type { User } from '../types/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User>()
  const checked = ref(false)
  async function restore() {
    if (checked.value) return user.value
    try { user.value = await authApi.getCurrentUser() }
    catch { user.value = undefined }
    finally { checked.value = true }
    return user.value
  }
  async function login(email: string, password: string) { user.value = await authApi.login(email, password); checked.value = true }
  async function register(email: string, password: string) { user.value = await authApi.register(email, password); checked.value = true }
  async function logout() { await authApi.logout(); user.value = undefined; checked.value = true }
  return { user, checked, restore, login, register, logout }
})
