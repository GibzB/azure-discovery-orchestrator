import { useRef, useEffect } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface ChatWindowProps {
  messages: Message[]
}

export default function ChatWindow({ messages }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="chat-window" role="log" aria-live="polite" aria-label="Conversation">
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`message message--${msg.role}`}
          aria-label={`${msg.role}: ${msg.content}`}
        >
          <span className="message__role">{msg.role === 'user' ? 'You' : 'Orchestrator'}</span>
          <p className="message__content">{msg.content}</p>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
