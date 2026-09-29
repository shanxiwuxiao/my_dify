import { requestJson } from './client'
import type { KnowledgeBase, KnowledgeDocument, KnowledgeSource, ListResponse } from '../types/api'
export const listKnowledgeBases = () => requestJson<ListResponse<KnowledgeBase>>('/api/knowledge-bases')
export const createKnowledgeBase = (name: string, description: string) => requestJson<KnowledgeBase>('/api/knowledge-bases', { method: 'POST', body: JSON.stringify({ name, description }) })
export const deleteKnowledgeBase = (id: string) => requestJson<void>(`/api/knowledge-bases/${id}`, { method: 'DELETE' })
export const listDocuments = (id: string) => requestJson<ListResponse<KnowledgeDocument>>(`/api/knowledge-bases/${id}/documents`)
export const addDocument = (id: string, name: string, content: string) => requestJson<KnowledgeDocument>(`/api/knowledge-bases/${id}/documents`, { method: 'POST', body: JSON.stringify({ name, content }) })
export const deleteDocument = (knowledgeId: string, documentId: string) => requestJson<void>(`/api/knowledge-bases/${knowledgeId}/documents/${documentId}`, { method: 'DELETE' })
export const searchKnowledge = (id: string, query: string) => requestJson<{ items: KnowledgeSource[] }>(`/api/knowledge-bases/${id}/search`, { method: 'POST', body: JSON.stringify({ query }) })
export const bindAppKnowledge = (appId: string, ids: string[]) => requestJson<{ knowledge_base_ids: string[] }>(`/api/apps/${appId}/knowledge-bases`, { method: 'PUT', body: JSON.stringify({ knowledge_base_ids: ids }) })
export const getAppKnowledge = (appId: string) => requestJson<{ knowledge_base_ids: string[] }>(`/api/apps/${appId}/knowledge-bases`)
