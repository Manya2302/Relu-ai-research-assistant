import type { ModelInfo, ProgressEvent, ResearchRequest } from '@/types/research'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

function getWsUrl(): string {
  if (API_BASE_URL) return API_BASE_URL.replace(/^http/, 'ws').replace(/\/$/, '') + '/api/ws/research'
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/api/ws/research`
}

export async function listGroqModels(groqApiKey: string): Promise<ModelInfo[]> {
  const response = await fetch(`${API_BASE_URL}/api/models`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ groq_api_key: groqApiKey }),
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || 'Failed to load Groq models.')
  }

  const payload = (await response.json()) as { models: ModelInfo[] }
  return payload.models
}

export async function runResearchStream(
  request: ResearchRequest,
  onProgress: (event: ProgressEvent) => void,
): Promise<ProgressEvent> {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(getWsUrl())

    socket.onopen = () => {
      socket.send(JSON.stringify(request))
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data as string) as ProgressEvent
      onProgress(data)
      if (data.error) {
        socket.close()
        reject(new Error(data.error))
        return
      }
      if (data.done || data.result) {
        socket.close()
        resolve(data)
      }
    }

    socket.onerror = () => {
      reject(new Error('Research stream disconnected unexpectedly.'))
    }
  })
}

export function downloadPdf(base64: string, filename: string) {
  const binary = atob(base64)
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0))
  const blob = new Blob([bytes], { type: 'application/pdf' })
  const url = window.URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename || 'company-research-report.pdf'
  anchor.click()
  window.URL.revokeObjectURL(url)
}
