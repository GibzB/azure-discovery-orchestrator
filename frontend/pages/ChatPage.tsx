import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import VoiceConversation from '../components/VoiceConversation'
import ChatWindow from '../components/ChatWindow'
import ChatInput from '../components/ChatInput'
import { useChat } from '../hooks/useChat'

type Mode = 'voice' | 'text'

export default function ChatPage() {
  const [mode, setMode] = useState<Mode>('voice')
  const { messages, sendMessage, loading, sessionId } = useChat()
  const navigate = useNavigate()

  const handleSessionComplete = () => {
    navigate(`/reports/${sessionId}`)
  }

  return (
    <main className="chat-page">
      <header className="chat-page__header">
        <h1>Azure Discovery Orchestrator</h1>
        <p>AI-powered architecture discovery — speak naturally or type your answers.</p>

        {/* Mode toggle */}
        <div className="chat-page__mode-toggle" role="group" aria-label="Interaction mode">
          <button
            className={`mode-btn ${mode === 'voice' ? 'mode-btn--active' : ''}`}
            onClick={() => setMode('voice')}
            aria-pressed={mode === 'voice'}
            type="button"
          >
            🎙 Voice
          </button>
          <button
            className={`mode-btn ${mode === 'text' ? 'mode-btn--active' : ''}`}
            onClick={() => setMode('text')}
            aria-pressed={mode === 'text'}
            type="button"
          >
            💬 Text
          </button>
        </div>
      </header>

      {mode === 'voice' ? (
        // ── Seamless voice conversation ──────────────────────────────────────
        <VoiceConversation
          sessionId={sessionId}
          onComplete={handleSessionComplete}
        />
      ) : (
        // ── Text fallback ────────────────────────────────────────────────────
        <>
          <ChatWindow messages={messages} />
          <ChatInput onSend={sendMessage} disabled={loading} />
        </>
      )}
    </main>
  )
}
