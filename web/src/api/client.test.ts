import { afterEach, describe, expect, it, vi } from 'vitest'
import { requestJson } from './client'

afterEach(() => vi.unstubAllGlobals())

describe('requestJson', () => {
  it('returns undefined for a successful 204 response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })))
    await expect(requestJson<void>('/resource', { method: 'DELETE' })).resolves.toBeUndefined()
  })

  it('preserves the API error code and status', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ code: 'unauthorized', message: 'Authentication required' }),
      { status: 401, headers: { 'Content-Type': 'application/json' } },
    )))
    await expect(requestJson('/private')).rejects.toMatchObject({
      status: 401,
      code: 'unauthorized',
      message: 'Authentication required',
    })
  })
})
