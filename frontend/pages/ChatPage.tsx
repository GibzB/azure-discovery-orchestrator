import { useState } from 'react'
import ChatWindow from '../components/ChatWindow'
import ChatInput from '../components/ChatInput'
import { useChat } from '../hooks/useChat'

export default function ChatPage() {
  const { messages, sendMessage, loading } = useChat()

  return (
    <main className="chat-page">
      <header>
        <h1>Azure Discovery Orchestrator</h1>
        <p>Describe your business — we'll design the right Azure architecture.</p>
      </header>
      <ChatWindow messages={messages} />
      <ChatInput onSend={sendMessage} disabled={loading} />
    </main>
  )
}
