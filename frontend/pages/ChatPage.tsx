import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import VoiceConversation from '../components/VoiceConversation'
import TextChat from '../components/TextChat'
import AppFooter from '../components/AppFooter'

type Mode = 'voice' | 'text'

export default function ChatPage() {
  const [mode, setMode] = useState<Mode>('voice')
  const [sessionId] = useState(() => crypto.randomUUID())
  const navigate = useNavigate()

  return (
    <>
      {/* ── Header ─────────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="brand">
          <div className="brand-logo" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
          </div>
          <div className="brand-text">
            <div className="brand-name">Discovery Orchestrator</div>
            <div className="brand-tagline">Powered by Azure AI</div>
          </div>
        </div>

        <div className="header-right">
          <div className="status-pill" aria-label="System status: online">
            <div className="status-dot" />
            System Online
          </div>

          <div className="mode-toggle" role="group" aria-label="Interaction mode">
            <button
              className={`mode-btn${mode === 'voice' ? ' mode-btn--active' : ''}`}
              onClick={() => setMode('voice')}
              aria-pressed={mode === 'voice'}
            >
              🎙 Voice
            </button>
            <button
              className={`mode-btn${mode === 'text' ? ' mode-btn--active' : ''}`}
              onClick={() => setMode('text')}
              aria-pressed={mode === 'text'}
            >
              💬 Text
            </button>
          </div>
        </div>
      </header>

      {/* ── Main ───────────────────────────────────────────────────── */}
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

      <AppFooter />
    </>
  )
}
