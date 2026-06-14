const BASE_URL = '/api/v1'

export const chatApi = {
  async send(sessionId: string, message: string): Promise<string> {
    const res = await fetch(`${BASE_URL}/chat/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message }),
    })
    if (!res.ok) throw new Error(`Chat API error: ${res.status}`)
    const data = await res.json()
    return data.response as string
  },
}
