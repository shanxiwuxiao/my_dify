export interface App {
  id: string
  name: string
  description: string
  system_prompt: string
  model_name: string
  temperature: number
  published_version: number | null
  provider_id: string | null
  created_at: string
  updated_at: string
}
export interface Conversation { id: string; app_id: string; name: string; created_at: string; updated_at: string }
export interface Message { id: string; conversation_id: string; role: 'user' | 'assistant'; content: string; status: string; created_at: string }
export interface ListResponse<T> {
  items: T[]
  total: number
}
export interface ApiError {
  code: string
  message: string
}
export interface CreateAppInput {
  name: string
  description: string
  system_prompt: string
  model_name: string
  temperature: number
  provider_id?: string | null
}
export type UpdateAppInput = CreateAppInput
export interface User { id: string; email: string; created_at: string }
export interface AppVersion { id: string; app_id: string; version: number; system_prompt: string; model_name: string; temperature: number; created_at: string }
export interface ModelProvider { id: string; name: string; base_url: string; default_model: string; api_key_masked: string; created_at: string }
export interface KnowledgeBase { id: string; name: string; description: string; created_at: string }
export interface KnowledgeDocument { id: string; knowledge_base_id: string; name: string; created_at: string }
export interface KnowledgeSource { segment_id: string; document_id: string; document_name: string; content: string; score: number }
export interface Workflow { id: string; name: string; app_id: string | null; definition: { nodes: unknown[]; edges: unknown[] }; created_at: string; updated_at: string }
export interface WorkflowRun { id: string; workflow_id: string; status: string; inputs: Record<string, unknown>; outputs: Record<string, unknown>; node_runs: Array<Record<string, unknown>>; error: string | null; created_at: string; finished_at: string | null }
