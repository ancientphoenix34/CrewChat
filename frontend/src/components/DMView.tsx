import React, { useEffect, useRef, useState } from 'react'
import { useParams, useLocation } from 'react-router-dom'
import api from '../api/client'
import { useAuthStore } from '../store/auth'

interface DirectMessage {
  id: string
  conversation_id: string
  sender_id: string
  content: string
  created_at: string
}

const WS_BASE = (import.meta.env.VITE_API_URL)
  .replace(/^http/, 'ws')

function dateLabel(iso: string): string {
  const d = new Date(iso)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)
  if (d.toDateString() === today.toDateString()) return 'Today'
  if (d.toDateString() === yesterday.toDateString()) return 'Yesterday'
  return d.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' })
}

function DateSeparator({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 my-2">
      <div className="flex-1 h-px bg-gray-100" />
      <span className="text-xs text-gray-400 font-medium">{label}</span>
      <div className="flex-1 h-px bg-gray-100" />
    </div>
  )
}

export default function DMView() {
  const { conversationId } = useParams<{ conversationId: string }>()
  const { state } = useLocation()
  const otherName: string = state?.displayName ?? 'Direct Message'

  const [messages, setMessages] = useState<DirectMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const typingThrottle = useRef<ReturnType<typeof setTimeout> | null>(null)
  const token = useAuthStore((s) => s.token)
  const currentUserId = useAuthStore((s) => s.user?.id)
  const currentUserName = useAuthStore((s) => s.user?.display_name)

  useEffect(() => {
    if (!conversationId) return
    setMessages([])
    setIsTyping(false)
    api.get(`/dms/${conversationId}/messages`).then(r => setMessages(r.data.messages))
  }, [conversationId])

  useEffect(() => {
    if (!conversationId || !token) return
    const ws = new WebSocket(`${WS_BASE}/dms/${conversationId}/ws?token=${token}`)
    wsRef.current = ws
    ws.onmessage = (e) => {
      const event = JSON.parse(e.data)
      if (event.type === 'typing') {
        setIsTyping(true)
        setTimeout(() => setIsTyping(false), 3000)
        return
      }
      const msg: DirectMessage = event
      setMessages(prev => [...prev, msg])
    }
    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [conversationId, token])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    setInput(e.target.value)
    if (wsRef.current?.readyState === WebSocket.OPEN && !typingThrottle.current) {
      wsRef.current.send(JSON.stringify({ type: 'typing', display_name: currentUserName }))
      typingThrottle.current = setTimeout(() => {
        typingThrottle.current = null
      }, 2000)
    }
  }

  async function doSend() {
    if (!input.trim() || sending || !conversationId) return
    setSending(true)
    try {
      await api.post(`/dms/${conversationId}/messages`, { content: input.trim() })
      setInput('')
    } finally {
      setSending(false)
    }
  }

  function handleSubmit(e: React.SyntheticEvent) {
    e.preventDefault()
    doSend()
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      doSend()
    }
  }

  function formatTime(iso: string) {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="flex flex-col h-screen">

      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-white shrink-0 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-700 text-sm font-bold">
          {otherName[0]?.toUpperCase()}
        </div>
        <div>
          <h2 className="font-semibold text-gray-900 text-sm">{otherName}</h2>
          <p className="text-xs text-gray-400">Direct Message</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 bg-white">
        {messages.length === 0 && (
          <p className="text-sm text-gray-400 text-center mt-10">
            Start a conversation with {otherName}.
          </p>
        )}
        <div className="space-y-3">
          {messages.map((msg, i) => {
            const isOwn = msg.sender_id === currentUserId
            const showSeparator =
              i === 0 ||
              new Date(msg.created_at).toDateString() !==
              new Date(messages[i - 1].created_at).toDateString()

            return (
              <React.Fragment key={msg.id}>
                {showSeparator && <DateSeparator label={dateLabel(msg.created_at)} />}
                <div className={`flex items-start gap-3 ${isOwn ? 'flex-row-reverse' : ''}`}>
                  <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-700 text-xs font-bold shrink-0 mt-0.5">
                    {isOwn ? currentUserName?.[0]?.toUpperCase() : otherName[0]?.toUpperCase()}
                  </div>
                  <div className={`max-w-xs lg:max-w-md flex flex-col ${isOwn ? 'items-end' : 'items-start'}`}>
                    <div className="flex items-baseline gap-2 mb-1">
                      <span className="text-xs font-semibold text-gray-700">
                        {isOwn ? 'You' : otherName}
                      </span>
                      <span className="text-xs text-gray-400">{formatTime(msg.created_at)}</span>
                    </div>
                    <div className={`px-3 py-2 rounded-2xl text-sm break-words ${
                      isOwn
                        ? 'bg-purple-600 text-white rounded-tr-sm'
                        : 'bg-gray-100 text-gray-800 rounded-tl-sm'
                    }`}>
                      {msg.content}
                    </div>
                  </div>
                </div>
              </React.Fragment>
            )
          })}
        </div>
        <div ref={bottomRef} />
      </div>

      {/* Typing indicator */}
      {isTyping && (
        <p className="text-xs text-gray-400 px-6 pb-1 bg-white">
          {otherName} is typing…
        </p>
      )}

      {/* Input */}
      <div className="px-6 py-4 border-t border-gray-200 bg-white shrink-0">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={`Message ${otherName}`}
            className="flex-1 border border-gray-200 rounded-lg px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-purple-400"
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="bg-purple-600 hover:bg-purple-700 disabled:opacity-40 text-white rounded-lg px-4 py-2.5 text-sm font-medium transition-colors"
          >
            Send
          </button>
        </form>
      </div>

    </div>
  )
}
