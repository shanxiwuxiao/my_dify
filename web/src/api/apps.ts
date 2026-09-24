import { requestJson } from './client'
import type { App, CreateAppInput, ListResponse } from '../types/api'

export const listApps = () => requestJson<ListResponse<App>>('/api/apps')
export const getApp = (id: string) => requestJson<App>(`/api/apps/${id}`)
export const createApp = (input: CreateAppInput) => requestJson<App>('/api/apps', { method: 'POST', body: JSON.stringify(input) })
