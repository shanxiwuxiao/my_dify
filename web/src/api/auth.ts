import { requestJson } from './client'
import type { User } from '../types/api'

export const getCurrentUser = () => requestJson<User>('/api/auth/me')
export const register = (email: string, password: string) => requestJson<User>('/api/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) })
export const login = (email: string, password: string) => requestJson<User>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })
export const logout = () => requestJson<void>('/api/auth/logout', { method: 'POST' })
