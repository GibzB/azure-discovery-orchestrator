import ChatWindow from '../components/ChatWindow'
import ChatInput from '../components/ChatInput'
import VoiceButton from '../components/VoiceButton'
import { useChat } from '../hooks/useChat'
import { useVoice } from '../hooks/useVoice'

export default function ChatPage() {
  const { messages, sendMessage, loading, sessionId } = useChat()

  const voice = useVoice({
    sessionId,
    onError: (msg) => console.error('[voice]', msg),
  })

  return (
    <main className="chat-page">
      <header>
        <h1>Azure Discovery Orchestrator</h1>
        <p>Describe your business — by text or voice — and we'll design the right Azure architecture.</p>
      </header>

      <ChatWindow messages={messages} />

      <div className="chat-page__input-row">
        {/* Text input */}
        <ChatInput onSend={sendMessage} disabled={loading || voice.state !== 'idle'} />

        {/* Voice button — hold to speak */}
        <VoiceButton
          state={voice.state}
          onStart={voice.startRecording}
          onStop={voice.stopRecording}
          onInterrupt={voice.stop}
          disabled={loading}
        />
      </div>

      {voice.errorMessage && (
        <p className="chat-page__voice-error" role="alert">
          {voice.errorMessage}
        </p>
      )}
    </main>
  )
}
