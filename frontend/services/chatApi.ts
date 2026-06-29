// Use VITE_API_BASE_URL when the SPA is hosted separately from the API (e.g. Blob Storage).
// Falls back to relative paths when running locally via the Vite dev proxy.
const API_ORIGIN = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? ''
const BASE_URL = `${API_ORIGIN}/api/v1`

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
