import {requestJson} from './client'
export interface AgentResult { answer:string; trace:Array<{step:number;tool:string;arguments:Record<string,unknown>;result:unknown}> }
export const runAgent=(appId:string,query:string)=>requestJson<AgentResult>(`/api/apps/${appId}/agent`,{method:'POST',body:JSON.stringify({query})})
