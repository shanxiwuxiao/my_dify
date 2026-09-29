import { requestJson } from './client'
import type { ListResponse, ModelProvider } from '../types/api'
export const listModelProviders = () => requestJson<ListResponse<ModelProvider>>('/api/model-providers')
export const createModelProvider = (input: { name: string; base_url: string; api_key: string; default_model: string }) => requestJson<ModelProvider>('/api/model-providers', { method: 'POST', body: JSON.stringify(input) })
export const deleteModelProvider = (id: string) => requestJson<void>(`/api/model-providers/${id}`, { method: 'DELETE' })
