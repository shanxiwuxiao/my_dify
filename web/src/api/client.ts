import type { ApiError } from '../types/api'

export class ApiRequestError extends Error {
  readonly status: number
  readonly code: string

  constructor(message: string, status: number, code = 'request_failed') {
    super(message)
    this.name = 'ApiRequestError'
    this.status = status
    this.code = code
  }
}

export async function requestJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options, headers: {
      ...(options?.body ? { 'Content-Type': 'application/json' } : {}),
      ...options?.headers,
    },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null) as ApiError | null
    throw new ApiRequestError(body?.message ?? `请求失败 (${response.status})`, response.status, body?.code)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}
