import { afterEach, describe, expect, it, vi } from 'vitest'
import { streamConversationMessage } from './stream'

afterEach(() => vi.unstubAllGlobals())

describe('streamConversationMessage', () => {
  it('reassembles SSE frames split across network chunks', async () => {
    const encoder = new TextEncoder()
    const body = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('event: message\ndata: {"del'))
        controller.enqueue(encoder.encode('ta":"你"}\n\nevent: sources\ndata: {"items":[]}\n\n'))
        controller.enqueue(encoder.encode('event: done\ndata: {}\n\n'))
        controller.close()
      },
    })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(body, { status: 200 })))
    const deltas: string[] = []
    let done = false
    await streamConversationMessage('conversation', 'hello', {
      onMessage: delta => deltas.push(delta),
      onDone: () => { done = true },
      onError: message => { throw new Error(message) },
    })
    expect(deltas).toEqual(['你'])
    expect(done).toBe(true)
  })
})
