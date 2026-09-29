import {requestJson} from './client'
export const getMonitoring=()=>requestJson<any>('/api/monitoring/summary')
export const listDatasets=()=>requestJson<any>('/api/evaluation-datasets')
export const createDataset=(name:string)=>requestJson<any>('/api/evaluation-datasets',{method:'POST',body:JSON.stringify({name})})
export const addCase=(id:string,input:string,expected:string)=>requestJson<any>(`/api/evaluation-datasets/${id}/cases`,{method:'POST',body:JSON.stringify({input,expected})})
export const runEvaluation=(id:string,appId:string)=>requestJson<any>(`/api/evaluation-datasets/${id}/runs`,{method:'POST',body:JSON.stringify({app_id:appId})})
