import { useState, useCallback } from 'react'
import { chatApi } from '../services/chatApi'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function useChat(existingSessionId?: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => existingSessionId ?? crypto.randomUUID())

  const sendMessage = useCallback(async (content: string) => {
    setMessages((prev) => [...prev, { role: 'user', content }])
    setLoading(true)
    try {
      const response = await chatApi.send(sessionId, content)
      setMessages((prev) => [...prev, { role: 'assistant', content: response }])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' },
      ])
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  return { messages, sendMessage, loading, sessionId }
}
