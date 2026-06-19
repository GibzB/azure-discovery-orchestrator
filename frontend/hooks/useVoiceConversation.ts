/**
 * useVoiceConversation — seamless WebSocket speech-to-speech conversation hook
 *
 * State machine:
 *
 *   disconnected
 *       ↓  connect()
 *   connecting
 *       ↓  WS open + send {type:"start"}
 *   speaking   ← server sends MP3 audio of opening question
 *       ↓  audio finishes playing  (auto-transition)
 *   listening  ← MediaRecorder starts automatically
 *       ↓  silence detected OR max duration reached
 *   processing ← audio sent to server
 *       ↓  server streams MP3 chunks back
 *   speaking   ← plays response
 *       ↓  audio finishes  →  listening  (seamless loop)
 *
 * The client NEVER has to press a button after the session starts.
 * Silence detection (VAD) stops recording automatically.
 */

import { useCallback, useEffect, useRef, useState } from 'react'

export type ConvState =
  | 'disconnected'
  | 'connecting'
  | 'listening'
  | 'processing'
  | 'speaking'
  | 'completed'
  | 'error'

interface Message {
  role: 'assistant' | 'user'
  text: string
}

interface UseVoiceConversationOptions {
  sessionId: string
  onMessage?: (msg: Message) => void
  onError?: (msg: string) => void
  onComplete?: () => void
  /** Milliseconds of silence before auto-stopping recording. Default: 1800 */
  silenceThresholdMs?: number
  /** Maximum recording duration in ms. Default: 30000 */
  maxRecordingMs?: number
}

const BASE_WS_URL = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`

export function useVoiceConversation({
  sessionId,
  onMessage: _onMessage,
  onError,
  onComplete,
  silenceThresholdMs = 1800,
  maxRecordingMs = 30000,
}: UseVoiceConversationOptions) {
  const [state, setState] = useState<ConvState>('disconnected')
  const [messages] = useState<Message[]>([])
  const [turn, setTurn] = useState(0)

  const wsRef = useRef<WebSocket | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const audioQueueRef = useRef<Blob[]>([])
  const isPlayingRef = useRef(false)
  const maxDurationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animFrameRef = useRef<number | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  // ── Audio playback queue ───────────────────────────────────────────────────
  const playNextChunk = useCallback(() => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false
      return
    }
    isPlayingRef.current = true
    const blob = audioQueueRef.current.shift()!
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    audio.onended = () => {
      URL.revokeObjectURL(url)
      playNextChunk()
    }
    audio.onerror = () => {
      URL.revokeObjectURL(url)
      playNextChunk()
    }
    audio.play().catch(console.error)
  }, [])

  const enqueueAudio = useCallback((bytes: ArrayBuffer) => {
    const blob = new Blob([bytes], { type: 'audio/mpeg' })
    audioQueueRef.current.push(blob)
    if (!isPlayingRef.current) playNextChunk()
  }, [playNextChunk])

  // ── Silence detection using Web Audio API ─────────────────────────────────
  const startSilenceDetection = useCallback((stream: MediaStream) => {
    const ctx = new AudioContext()
    const source = ctx.createMediaStreamSource(stream)
    const analyser = ctx.createAnalyser()
    analyser.fftSize = 512
    source.connect(analyser)
    analyserRef.current = analyser

    const data = new Uint8Array(analyser.frequencyBinCount)
    let lastSoundTime = Date.now()

    const tick = () => {
      analyser.getByteFrequencyData(data)
      const volume = data.reduce((a, b) => a + b, 0) / data.length
      if (volume > 8) lastSoundTime = Date.now()           // sound detected
      const silent = Date.now() - lastSoundTime > silenceThresholdMs
      if (silent && recorderRef.current?.state === 'recording') {
        stopRecording()
        return
      }
      animFrameRef.current = requestAnimationFrame(tick)
    }
    animFrameRef.current = requestAnimationFrame(tick)
  }, [silenceThresholdMs])

  // ── Recording ──────────────────────────────────────────────────────────────
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      chunksRef.current = []

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'
      const recorder = new MediaRecorder(stream, { mimeType })

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop())
        if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
        const blob = new Blob(chunksRef.current, { type: mimeType })
        sendAudio(blob)
      }

      recorder.start(100) // collect data every 100ms
      recorderRef.current = recorder
      setState('listening')

      startSilenceDetection(stream)

      // Safety: max recording duration
      maxDurationTimerRef.current = setTimeout(() => {
        if (recorderRef.current?.state === 'recording') stopRecording()
      }, maxRecordingMs)

    } catch {
      setState('error')
      onError?.('Microphone access denied.')
    }
  }, [silenceThresholdMs, maxRecordingMs, startSilenceDetection])

  const stopRecording = useCallback(() => {
    if (maxDurationTimerRef.current) clearTimeout(maxDurationTimerRef.current)
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.stop()
      setState('processing')
    }
  }, [])

  // ── Send audio over WebSocket ──────────────────────────────────────────────
  const sendAudio = useCallback(async (blob: Blob) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    const buffer = await blob.arrayBuffer()
    wsRef.current.send(buffer)
  }, [])

  // ── WebSocket connection ───────────────────────────────────────────────────
  const connect = useCallback(() => {
    if (wsRef.current) return
    setState('connecting')

    const ws = new WebSocket(`${BASE_WS_URL}/api/v1/voice/ws/${sessionId}`)
    ws.binaryType = 'arraybuffer'
    wsRef.current = ws

    ws.onopen = () => {
      // Request the opening greeting immediately
      ws.send(JSON.stringify({ type: 'start' }))
      setState('speaking')
    }

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        // MP3 audio chunk — enqueue for playback
        enqueueAudio(event.data)
        setState('speaking')
      } else {
        // JSON control frame
        try {
          const data = JSON.parse(event.data as string)

          if (data.type === 'turn_end') {
            setTurn(data.turn ?? 0)
            if (data.is_final) {
              setState('completed')
              onComplete?.()
            } else {
              // Wait for audio queue to drain, then auto-start listening
              const waitAndListen = () => {
                if (isPlayingRef.current || audioQueueRef.current.length > 0) {
                  setTimeout(waitAndListen, 100)
                } else {
                  setState('listening')
                  startRecording()
                }
              }
              waitAndListen()
            }
          } else if (data.type === 'error') {
            onError?.(data.message)
            setState('error')
          } else if (data.type === 'session_ended') {
            setState('completed')
            onComplete?.()
          }
        } catch {
          // ignore parse errors
        }
      }
    }

    ws.onerror = () => {
      setState('error')
      onError?.('WebSocket connection error.')
    }

    ws.onclose = () => {
      wsRef.current = null
      if (state !== 'completed') setState('disconnected')
    }
  }, [sessionId, enqueueAudio, startRecording, onError, onComplete])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: 'end' }))
      wsRef.current.close()
      wsRef.current = null
    }
    recorderRef.current?.stop()
    streamRef.current?.getTracks().forEach((t) => t.stop())
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
    setState('disconnected')
  }, [])

  // Cleanup on unmount
  useEffect(() => () => disconnect(), [disconnect])

  return {
    state,
    messages,
    turn,
    connect,
    disconnect,
    isActive: state !== 'disconnected' && state !== 'completed' && state !== 'error',
  }
}
