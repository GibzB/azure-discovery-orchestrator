import { useVoiceConversation, type ConvState } from '../hooks/useVoiceConversation'

interface Props {
  sessionId: string
  onComplete?: () => void
}

const ORB_ICON: Record<ConvState, string> = {
  disconnected: '🎙', connecting: '⟳',
  listening: '👂', processing: '⟳',
  speaking: '🔊', completed: '✓', error: '⚠',
}

const STATUS_TEXT: Record<ConvState, string> = {
  disconnected: 'Ready to begin your discovery session',
  connecting:   'Connecting to your AI consultant…',
  listening:    'Listening — speak now',
  processing:   'Processing your response…',
  speaking:     'Your consultant is speaking',
  completed:    'Session complete — preparing your report',
  error:        'Connection lost — please try again',
}

const STATUS_CLASS: Partial<Record<ConvState, string>> = {
  listening: 'orb-label--listening',
  speaking:  'orb-label--speaking',
  completed: 'orb-label--completed',
  error:     'orb-label--error',
}

const PHASES = ['Business', 'Technical', 'Compliance', 'Report']

export default function VoiceConversation({ sessionId: _sessionId, onComplete }: Props) {
  const { state, messages, turn, connect, disconnect, isActive } =
    useVoiceConversation({ sessionId: _sessionId, onComplete })

  const phase = Math.min(Math.floor((turn - 1) / 4), 3)
  const isSpeaking = state === 'speaking'
  const isListening = state === 'listening'
  const isIdle = state === 'disconnected' || state === 'error'

  return (
    <>
      <div className="glass-card">
        <div className="hero-section">
          {/* Badge */}
          <div className="hero-badge">
            <span>✦</span> AI Architecture Discovery
          </div>

          {/* Title */}
          <h1 className="hero-title">
            Meet your Azure<br />Solutions Architect
          </h1>
          <p className="hero-sub">
            Speak naturally about your business. Your AI consultant will ask
            focused questions and design the right Azure architecture for you —
            all in a single conversation.
          </p>

          {/* Feature pills */}
          <div className="features">
            {[
              { icon: '🎙', label: 'Voice-first' },
              { icon: '🧠', label: 'GPT-4.1 powered' },
              { icon: '📋', label: 'Instant report' },
              { icon: '🔒', label: 'Enterprise secure' },
            ].map(f => (
              <div key={f.label} className="feature-pill">
                <span className="feature-pill-icon">{f.icon}</span> {f.label}
              </div>
            ))}
          </div>

          {/* Phase steps — only show during session */}
          {isActive && (
            <div className="steps" aria-label="Discovery phases">
              {PHASES.map((p, i) => (
                <>
                  {i > 0 && <div key={`line-${i}`} className="step-line" />}
                  <div
                    key={p}
                    className={`step${i === phase ? ' step--active' : i < phase ? ' step--done' : ''}`}
                    aria-current={i === phase ? 'step' : undefined}
                  >
                    <div className="step-num">{i < phase ? '✓' : i + 1}</div>
                    <div className="step-label">{p}</div>
                  </div>
                </>
              ))}
            </div>
          )}

          {/* Orb */}
          <div className="orb-container" aria-live="polite" aria-atomic="true">
            <div className={`orb-ring orb-ring-1${isListening ? ' orb-ring--listening' : isSpeaking ? ' orb-ring--speaking' : ''}`} aria-hidden="true" />
            <div className={`orb-ring orb-ring-2${isListening ? ' orb-ring--listening' : isSpeaking ? ' orb-ring--speaking' : ''}`} aria-hidden="true" />

            <button
              className={`orb-btn orb-btn--${state}`}
              onClick={() => isIdle ? connect() : state === 'speaking' ? disconnect() : undefined}
              aria-label={STATUS_TEXT[state]}
              aria-pressed={isActive}
              disabled={state === 'connecting' || state === 'processing'}
            >
              {isSpeaking ? (
                <div className="waveform waveform--active" aria-hidden="true">
                  {[...Array(5)].map((_, i) => <div key={i} className="waveform-bar" />)}
                </div>
              ) : (
                <span className="orb-icon" aria-hidden="true">{ORB_ICON[state]}</span>
              )}
              {isActive && turn > 0 && (
                <div className="orb-pill">Q{turn}</div>
              )}
            </button>
          </div>

          {/* Status */}
          <p className={`orb-label ${STATUS_CLASS[state] || ''}`}>
            {STATUS_TEXT[state]}
          </p>

          {/* CTA / controls */}
          <div className="cta-group">
            {isIdle && (
              <>
                <button className="cta-primary" onClick={connect}>
                  <span>🎙</span> Start Discovery Session
                </button>
                <p className="cta-hint">
                  Click the orb or press <kbd>Space</kbd> to begin
                </p>
              </>
            )}
            {isActive && (
              <button className="end-btn" onClick={disconnect}>
                ✕ End Session
              </button>
            )}
          </div>

          {/* Error */}
          {state === 'error' && (
            <div className="error-alert" role="alert">
              ⚠ Check your microphone permissions and network connection, then try again.
            </div>
          )}
        </div>
      </div>

      {/* Live transcript */}
      {messages.length > 0 && (
        <div className="transcript-card" aria-label="Live conversation transcript">
          <div className="transcript-header">
            <span className="transcript-title">Live Transcript</span>
            {isActive && <div className="rec-dot" aria-label="Recording in progress" />}
          </div>
          <div className="transcript-body">
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
