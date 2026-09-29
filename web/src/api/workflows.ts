import { requestJson } from './client'
import type { ListResponse, Workflow, WorkflowRun } from '../types/api'
export const listWorkflows=()=>requestJson<ListResponse<Workflow>>('/api/workflows')
export const createWorkflow=(name:string,definition:unknown,appId:string|null=null)=>requestJson<Workflow>('/api/workflows',{method:'POST',body:JSON.stringify({name,definition,app_id:appId})})
export const updateWorkflow=(id:string,name:string,definition:unknown,appId:string|null=null)=>requestJson<Workflow>(`/api/workflows/${id}`,{method:'PUT',body:JSON.stringify({name,definition,app_id:appId})})
export const deleteWorkflow=(id:string)=>requestJson<void>(`/api/workflows/${id}`,{method:'DELETE'})
export const runWorkflow=(id:string,inputs:Record<string,unknown>)=>requestJson<WorkflowRun>(`/api/workflows/${id}/runs`,{method:'POST',body:JSON.stringify({inputs})})
export const listWorkflowRuns=(id:string)=>requestJson<ListResponse<WorkflowRun>>(`/api/workflows/${id}/runs`)
