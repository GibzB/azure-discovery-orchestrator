/**
 * useVoice — speech-to-speech hook
 *
 * Records from the microphone, sends the audio to POST /api/v1/voice/turn,
 * receives MP3 audio bytes back, and plays them through the browser speaker.
 *
 * State machine:
 *   idle → recording → processing → speaking → idle
 */
import { useCallback, useRef, useState } from 'react'

export type VoiceState = 'idle' | 'recording' | 'processing' | 'speaking' | 'error'

interface UseVoiceOptions {
  sessionId: string
  onTranscript?: (text: string) => void  // called with STT result if API returns it
  onError?: (msg: string) => void
}

export function useVoice({ sessionId, onError }: UseVoiceOptions) {
  const [state, setState] = useState<VoiceState>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const setError = (msg: string) => {
    setErrorMessage(msg)
    setState('error')
    onError?.(msg)
  }

  // ── Start recording ────────────────────────────────────────────────────────
  const startRecording = useCallback(async () => {
    if (state !== 'idle' && state !== 'error') return

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'

      const recorder = new MediaRecorder(stream, { mimeType })
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        // Stop all tracks so the mic indicator turns off
        stream.getTracks().forEach((t) => t.stop())
        await sendAudio(new Blob(chunksRef.current, { type: mimeType }))
      }

      recorder.start()
      mediaRecorderRef.current = recorder
      setState('recording')
    } catch (err) {
      setError('Microphone access denied or unavailable.')
    }
  }, [state, sessionId])

  // ── Stop recording ─────────────────────────────────────────────────────────
  const stopRecording = useCallback(() => {
    if (state !== 'recording') return
    setState('processing')
    mediaRecorderRef.current?.stop()
  }, [state])

  // ── Send audio to backend and play response ────────────────────────────────
  const sendAudio = async (blob: Blob) => {
    setState('processing')
    try {
      const form = new FormData()
      form.append('session_id', sessionId)
      form.append('audio', blob, 'recording.webm')

      const res = await fetch('/api/v1/voice/turn', {
        method: 'POST',
        body: form,
      })

      if (!res.ok) {
        const detail = await res.text()
        throw new Error(detail || `HTTP ${res.status}`)
      }

      const audioBlob = await res.blob()
      const url = URL.createObjectURL(audioBlob)

      setState('speaking')
      const audio = new Audio(url)
      audioRef.current = audio

      audio.onended = () => {
        URL.revokeObjectURL(url)
        setState('idle')
      }

      audio.onerror = () => {
        URL.revokeObjectURL(url)
        setError('Failed to play audio response.')
      }

      await audio.play()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Voice request failed.')
    }
  }

  // ── Interrupt playback ─────────────────────────────────────────────────────
  const stop = useCallback(() => {
    audioRef.current?.pause()
    setState('idle')
  }, [])

  return {
    state,
    errorMessage,
    isRecording: state === 'recording',
    isProcessing: state === 'processing',
    isSpeaking: state === 'speaking',
    startRecording,
    stopRecording,
    stop,
  }
}
