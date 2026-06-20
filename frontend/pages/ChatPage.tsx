import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import VoiceConversation from '../components/VoiceConversation'
import TextChat from '../components/TextChat'

type Mode = 'voice' | 'text'

export default function ChatPage() {
  const [mode, setMode] = useState<Mode>('voice')
  const [sessionId] = useState(() => crypto.randomUUID())
  const navigate = useNavigate()

  return (
    <>
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="brand">
          <div className="brand-icon" aria-hidden="true">⬡</div>
          <div>
            <div className="brand-name">Azure Discovery Orchestrator</div>
          </div>
          <span className="brand-sub">— AI Architecture Discovery</span>
        </div>

        {/* Mode toggle */}
        <div
          className="mode-toggle"
          role="group"
          aria-label="Choose interaction mode"
        >
          <button
            className={`mode-btn ${mode === 'voice' ? 'mode-btn--active' : ''}`}
            onClick={() => setMode('voice')}
            aria-pressed={mode === 'voice'}
          >
            🎙 Voice
          </button>
          <button
            className={`mode-btn ${mode === 'text' ? 'mode-btn--active' : ''}`}
            onClick={() => setMode('text')}
            aria-pressed={mode === 'text'}
          >
            💬 Text
          </button>
        </div>
      </header>

      {/* ── Main ───────────────────────────────────────────────────────── */}
      <main className="page-main">
        {mode === 'voice' ? (
          <VoiceConversation
            sessionId={sessionId}
            onComplete={() => navigate(`/reports/${sessionId}`)}
          />
        ) : (
          <TextChat sessionId={sessionId} />
        )}
      </main>
    </>
  )
}
