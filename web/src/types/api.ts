export interface App { id: string; name: string; description: string; system_prompt: string; model_name: string; temperature: number; created_at: string; updated_at: string }
export interface Conversation { id: string; app_id: string; name: string; created_at: string; updated_at: string }
export interface Message { id: string; conversation_id: string; role: 'user' | 'assistant'; content: string; status: string; created_at: string }
export interface ListResponse<T> { items: T[]; total: number }
export interface ApiError { code: string; message: string }
export interface CreateAppInput { name: string; description: string; system_prompt: string; model_name: string; temperature: number }
