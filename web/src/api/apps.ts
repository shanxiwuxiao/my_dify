import { requestJson } from './client'
import type { App, AppVersion, CreateAppInput, ListResponse, UpdateAppInput } from '../types/api'

export const listApps = () => requestJson<ListResponse<App>>('/api/apps')
export const getApp = (id: string) => requestJson<App>(`/api/apps/${id}`)
export const createApp = (input: CreateAppInput) => requestJson<App>('/api/apps', { method: 'POST', body: JSON.stringify(input) })
export const updateApp = (id: string, input: UpdateAppInput) => requestJson<App>(`/api/apps/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
export const deleteApp = (id: string) => requestJson<void>(`/api/apps/${id}`, { method: 'DELETE' })
export const publishApp = (id: string) => requestJson<AppVersion>(`/api/apps/${id}/publish`, { method: 'POST' })
export const listAppVersions = (id: string) => requestJson<ListResponse<AppVersion>>(`/api/apps/${id}/versions`)
export const debugApp = (id: string, message: string) => requestJson<{ answer: string }>(`/api/apps/${id}/chat`, { method: 'POST', body: JSON.stringify({ message }) })
