import { useVoiceConversation, type ConvState } from '../hooks/useVoiceConversation'

interface Props {
  sessionId: string
  onComplete?: () => void
}

/* ── State → display mapping ──────────────────────────────────────────────── */
const ICON: Record<ConvState, string> = {
  disconnected: '🎙',
  connecting:   '⟳',
  listening:    '👂',
  processing:   '⟳',
  speaking:     '🔊',
  completed:    '✓',
  error:        '⚠',
}

const LABEL: Record<ConvState, string> = {
  disconnected: 'Press to start your discovery session',
  connecting:   'Connecting…',
  listening:    'Listening — speak now',
  processing:   'Processing your answer…',
  speaking:     'Azure Consultant is speaking',
  completed:    'Session complete — your report is being prepared',
  error:        'Something went wrong — please try again',
}

const STATUS_CLASS: Partial<Record<ConvState, string>> = {
  listening: 'status-label--listening',
  speaking:  'status-label--speaking',
  error:     'status-label--error',
}

export default function VoiceConversation({ sessionId, onComplete }: Props) {
  const { state, messages, turn, connect, disconnect, isActive } =
    useVoiceConversation({ sessionId, onComplete })

  const handleOrb = () => {
    if (state === 'disconnected' || state === 'error') connect()
    else if (state === 'speaking') disconnect()
  }

  const isSpeaking = state === 'speaking'
  const isListening = state === 'listening'

  return (
    <>
      {/* ── Hero card ────────────────────────────────────────────────── */}
      <div className="hero-card">
        <p className="hero-greeting">Azure Architecture Discovery</p>
        <h1 className="hero-title">Your AI Consultant is ready</h1>
        <p className="hero-subtitle">
          Start a voice session and describe your business. Your consultant will
          ask questions and design the right Azure architecture for you.
        </p>

        {/* Orb */}
        <div className="orb-wrapper" aria-live="polite">
          <div className={`orb-ring ${isSpeaking ? 'orb-ring--speaking' : isListening ? 'orb-ring--active' : ''}`} aria-hidden="true" />
          <button
            className={`orb-btn orb-btn--${state}`}
            onClick={handleOrb}
            aria-label={LABEL[state]}
            aria-pressed={isActive}
            disabled={state === 'connecting' || state === 'processing'}
          >
            {/* Waveform when speaking, icon otherwise */}
            {isSpeaking ? (
              <div className={`waveform waveform--speaking`} aria-hidden="true">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="waveform-bar" />
                ))}
              </div>
            ) : (
              <span className="orb-icon" aria-hidden="true">{ICON[state]}</span>
            )}
            {isActive && turn > 0 && (
              <span className="orb-turn">Q{turn}</span>
            )}
          </button>
        </div>

        {/* Status */}
        <p className={`status-label ${STATUS_CLASS[state] || ''}`}>
          {LABEL[state]}
        </p>

        {/* CTA when idle */}
        {(state === 'disconnected' || state === 'error') && (
          <>
            <button className="cta-btn" onClick={connect}>
              <span>🎙</span> Start Discovery Session
            </button>
            <p className="cta-hint">
              Hold Space to speak • Click orb to start
            </p>
          </>
        )}

        {/* End session when active */}
        {isActive && (
          <button className="end-btn" onClick={disconnect} aria-label="End session">
            ✕ End Session
          </button>
        )}

        {/* Error */}
        {state === 'error' && (
          <div className="error-banner" role="alert" style={{ marginTop: 16 }}>
            ⚠ Connection lost. Check your microphone permissions and try again.
          </div>
        )}
      </div>

      {/* ── Live transcript ───────────────────────────────────────────── */}
      {messages.length > 0 && (
        <div className="transcript-card" aria-label="Conversation transcript" aria-live="polite">
          <div className="transcript-header">
            <span className="transcript-title">Live Transcript</span>
            {isActive && <div className="rec-dot" aria-label="Recording" />}
          </div>
          <div className="transcript-body" id="transcript-body">
            {messages.map((m, i) => (
              <div key={i} className={`msg msg--${m.role}`}>
                <span className="msg__role">{m.role === 'assistant' ? 'Consultant' : 'You'}</span>
                <div className="msg__bubble">{m.text}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
