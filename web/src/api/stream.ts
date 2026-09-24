export interface StreamHandlers { onMessage: (delta: string) => void; onDone: () => void; onError: (message: string) => void }
interface SsePayload { delta?: string; message?: string }

function dispatchFrame(frame: string, handlers: StreamHandlers) {
  let event = 'message'
  const dataLines: string[] = []
  for (const line of frame.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart())
  }
  if (!dataLines.length) return
  let payload: SsePayload
  try { payload = JSON.parse(dataLines.join('\n')) as SsePayload }
  catch { handlers.onError('服务器返回了无法解析的流式数据'); return }
  if (event === 'message') handlers.onMessage(payload.delta ?? '')
  else if (event === 'done') handlers.onDone()
  else if (event === 'error') handlers.onError(payload.message ?? '模型请求失败')
}

export async function streamConversationMessage(conversationId: string, message: string, handlers: StreamHandlers, signal?: AbortSignal) {
  const response = await fetch(`/api/conversations/${conversationId}/messages/stream`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message }), signal,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => null) as { message?: string } | null
    throw new Error(error?.message ?? `请求失败 (${response.status})`)
  }
  if (!response.body) throw new Error('浏览器不支持流式响应')
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, '\n')
    const frames = buffer.split('\n\n')
    buffer = frames.pop() ?? ''
    for (const frame of frames) dispatchFrame(frame, handlers)
    if (done) break
  }
  if (buffer.trim()) dispatchFrame(buffer, handlers)
}
