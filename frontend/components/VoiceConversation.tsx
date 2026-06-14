/**
 * VoiceConversation — full-screen seamless voice discovery UI
 *
 * Shows a single ambient orb that pulses based on conversation state:
 *   disconnected  → flat grey ring  "Start Discovery"
 *   connecting    → slow pulse
 *   speaking      → animated wave (assistant is talking)
 *   listening     → bright green pulse (we're hearing you)
 *   processing    → rotating arc (thinking)
 *   completed     → checkmark
 *   error         → red
 */
import { useEffect } from 'react'
import { useVoiceConversation, type ConvState } from '../hooks/useVoiceConversation'

interface VoiceConversationProps {
  sessionId: string
  onComplete?: () => void
}

const STATE_LABEL: Record<ConvState, string> = {
  disconnected: 'Press to start your discovery session',
  connecting:   'Connecting…',
  listening:    'Listening — speak now',
  processing:   'Processing your answer…',
  speaking:     'Azure Discovery Consultant is speaking',
  completed:    'Session complete — your report is being prepared',
  error:        'Something went wrong — please refresh',
}

const STATE_ICON: Record<ConvState, string> = {
  disconnected: '🎙',
  connecting:   '⟳',
  listening:    '👂',
  processing:   '⟳',
  speaking:     '🔊',
  completed:    '✓',
  error:        '⚠',
}

export default function VoiceConversation({ sessionId, onComplete }: VoiceConversationProps) {
  const { state, turn, connect, disconnect, isActive } = useVoiceConversation({
    sessionId,
    onComplete,
    onError: (msg) => console.error('[voice]', msg),
  })

  const handleClick = () => {
    if (state === 'disconnected' || state === 'error') {
      connect()
    } else if (isActive) {
      disconnect()
    }
  }

  return (
    <div className="voice-conversation" aria-live="polite">
      {/* Ambient orb */}
      <button
        className={`voice-orb voice-orb--${state}`}
        onClick={handleClick}
        aria-label={STATE_LABEL[state]}
        aria-pressed={isActive}
        disabled={state === 'connecting' || state === 'processing'}
        type="button"
      >
        <span className="voice-orb__icon" aria-hidden="true">
          {STATE_ICON[state]}
        </span>
      </button>

      {/* State label */}
      <p className="voice-conversation__label">{STATE_LABEL[state]}</p>

      {/* Turn counter */}
      {isActive && (
        <p className="voice-conversation__turn" aria-label={`Turn ${turn}`}>
          Turn {turn}
        </p>
      )}

      {/* Stop button when active */}
      {isActive && (
        <button
          className="voice-conversation__stop"
          onClick={disconnect}
          aria-label="End session"
          type="button"
        >
          End session
        </button>
      )}
    </div>
  )
}
