import { KeyboardEvent, useRef, useEffect } from 'react'
import { useChat } from '../hooks/useChat'

interface Props { sessionId: string }

export default function TextChat({ sessionId }: Props) {
  const { messages, sendMessage, loading } = useChat(sessionId)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const submit = () => {
    const val = textareaRef.current?.value.trim()
    if (!val || loading) return
    sendMessage(val)
    if (textareaRef.current) textareaRef.current.value = ''
  }

  return (
    <div className="chat-window" role="log" aria-label="Chat conversation">
      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">💬</div>
            <strong>Start the conversation</strong>
            <p>Describe your company, industry, or technical needs below.</p>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`msg msg--${m.role}`}>
              <span className="msg__role">{m.role === 'assistant' ? 'Consultant' : 'You'}</span>
              <div className="msg__bubble">{m.content}</div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="chat-input-row">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder="Describe your business needs… (Enter to send)"
          onKeyDown={handleKeyDown}
          disabled={loading}
          rows={1}
          aria-label="Type your message"
        />
        <button
          className="send-btn"
          onClick={submit}
          disabled={loading}
          aria-label="Send message"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  )
}
