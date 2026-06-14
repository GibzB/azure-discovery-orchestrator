/**
 * VoiceButton — push-to-talk UI component
 *
 * Hold to record, release to send.
 * Displays state-aware feedback: idle / recording / processing / speaking / error.
 */
import { useEffect } from 'react'
import { type VoiceState } from '../hooks/useVoice'

interface VoiceButtonProps {
  state: VoiceState
  onStart: () => void
  onStop: () => void
  onInterrupt: () => void
  disabled?: boolean
}

const LABELS: Record<VoiceState, string> = {
  idle: 'Hold to speak',
  recording: 'Recording… release to send',
  processing: 'Processing…',
  speaking: 'Speaking — click to stop',
  error: 'Error — click to retry',
}

const ARIA_LABELS: Record<VoiceState, string> = {
  idle: 'Start voice input',
  recording: 'Stop recording',
  processing: 'Processing your voice input',
  speaking: 'Stop speaking',
  error: 'Retry voice input',
}

export default function VoiceButton({
  state,
  onStart,
  onStop,
  onInterrupt,
  disabled = false,
}: VoiceButtonProps) {
  // Keyboard: Space = push-to-talk
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code !== 'Space' || e.repeat || disabled) return
      if (state === 'idle' || state === 'error') onStart()
    }
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code !== 'Space' || disabled) return
      if (state === 'recording') onStop()
    }
    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
    }
  }, [state, disabled, onStart, onStop])

  const handleClick = () => {
    if (disabled) return
    if (state === 'speaking') { onInterrupt(); return }
    if (state === 'recording') { onStop(); return }
    if (state === 'idle' || state === 'error') { onStart(); return }
  }

  const handleMouseDown = () => {
    if (disabled || state !== 'idle') return
    onStart()
  }

  const handleMouseUp = () => {
    if (disabled || state !== 'recording') return
    onStop()
  }

  return (
    <div className="voice-button-wrapper">
      <button
        className={`voice-button voice-button--${state}`}
        aria-label={ARIA_LABELS[state]}
        aria-pressed={state === 'recording'}
        aria-busy={state === 'processing'}
        disabled={disabled || state === 'processing'}
        onClick={handleClick}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onTouchStart={(e) => { e.preventDefault(); handleMouseDown() }}
        onTouchEnd={(e) => { e.preventDefault(); handleMouseUp() }}
        type="button"
      >
        <MicIcon state={state} />
      </button>
      <span className="voice-button__label" aria-live="polite">
        {LABELS[state]}
      </span>
    </div>
  )
}

function MicIcon({ state }: { state: VoiceState }) {
  if (state === 'processing') {
    return <span className="voice-icon voice-icon--spinner" aria-hidden="true">⟳</span>
  }
  if (state === 'speaking') {
    return <span className="voice-icon voice-icon--speaking" aria-hidden="true">🔊</span>
  }
  if (state === 'error') {
    return <span className="voice-icon voice-icon--error" aria-hidden="true">⚠</span>
  }
  return (
    <span
      className={`voice-icon voice-icon--mic ${state === 'recording' ? 'voice-icon--active' : ''}`}
      aria-hidden="true"
    >
      🎙
    </span>
  )
}
