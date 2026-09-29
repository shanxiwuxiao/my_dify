import { requestJson } from './client'
import type { Conversation, ListResponse, Message } from '../types/api'

export const listConversations = (appId: string) => requestJson<ListResponse<Conversation>>(`/api/apps/${appId}/conversations`)
export const createConversation = (appId: string, name: string) => requestJson<Conversation>(`/api/apps/${appId}/conversations`, { method: 'POST', body: JSON.stringify({ name }) })
export const getConversation = (id: string) => requestJson<Conversation>(`/api/conversations/${id}`)
export const getMessages = (id: string) => requestJson<ListResponse<Message>>(`/api/conversations/${id}/messages`)
export const renameConversation = (id: string, name: string) => requestJson<Conversation>(`/api/conversations/${id}`, { method: 'PATCH', body: JSON.stringify({ name }) })
export const deleteConversation = (id: string) => requestJson<void>(`/api/conversations/${id}`, { method: 'DELETE' })
