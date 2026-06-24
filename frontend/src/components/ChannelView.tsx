import React, { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client'
import { useAuthStore } from '../store/auth'

interface Message {
  id: string
  channel_id: string
  sender_id: string
  content: string
  created_at: string
}

interface Channel {
  id: string
  name: string
  description: string | null
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

export default function ChannelView() {
  const { channelId } = useParams<{ channelId: string }>()
  const [channel, setChannel] = useState<Channel | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [typingUsers, setTypingUsers] = useState<string[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const typingThrottle = useRef<ReturnType<typeof setTimeout> | null>(null)
  const token = useAuthStore((s) => s.token)
  const currentUserId = useAuthStore((s) => s.user?.id)
  const currentUserName = useAuthStore((s) => s.user?.display_name)
  const [memberMap, setMemberMap] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!channelId) return
    setMessages([])
    setChannel(null)
    setTypingUsers([])
    api.patch(`/channels/${channelId}/read`).catch(() => {})
    api.get(`/channels/${channelId}`).then(r => setChannel(r.data))
    api.get(`/channels/${channelId}/messages`).then(r => setMessages(r.data.messages))
    api.get('/auth/members').then(r => {
      const map: Record<string, string> = {}
      for (const m of r.data) map[m.id] = m.display_name
      if (currentUserId && currentUserName) map[currentUserId] = currentUserName
      setMemberMap(map)
    })
  }, [channelId])

  useEffect(() => {
    if (!channelId || !token) return
    const ws = new WebSocket(`${WS_BASE}/channels/${channelId}/ws?token=${token}`)
    wsRef.current = ws
    ws.onmessage = (e) => {
      const event = JSON.parse(e.data)
      if (event.type === 'typing') {
        setTypingUsers(prev =>
          prev.includes(event.display_name) ? prev : [...prev, event.display_name]
        )
        setTimeout(() => {
          setTypingUsers(prev => prev.filter(n => n !== event.display_name))
        }, 3000)
        return
      }
      const msg: Message = event
      setMessages(prev => [...prev, msg])
    }
    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [channelId, token])

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
    if (!input.trim() || sending || !channelId) return
    setSending(true)
    try {
      await api.post(`/channels/${channelId}/messages`, { content: input.trim() })
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

      {/* Channel header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-white shrink-0">
        <h2 className="font-semibold text-gray-900 flex items-center gap-1.5">
          <span className="text-gray-400">#</span>
          {channel?.name ?? '…'}
        </h2>
        {channel?.description && (
          <p className="text-xs text-gray-400 mt-0.5">{channel.description}</p>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 bg-white">
        {messages.length === 0 && (
          <p className="text-sm text-gray-400 text-center mt-10">
            No messages yet. Say hello!
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
                <div className="flex items-start gap-3 group">
                  <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-700 text-xs font-bold shrink-0 mt-0.5">
                    {(memberMap[msg.sender_id] ?? msg.sender_id)[0].toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline gap-2">
                      <span className={`text-sm font-semibold ${isOwn ? 'text-purple-700' : 'text-gray-800'}`}>
                        {memberMap[msg.sender_id] ?? msg.sender_id.slice(0, 8)}
                      </span>
                      <span className="text-xs text-gray-400">{formatTime(msg.created_at)}</span>
                    </div>
                    <p className="text-sm text-gray-700 break-words">{msg.content}</p>
                  </div>
                </div>
              </React.Fragment>
            )
          })}
        </div>
        <div ref={bottomRef} />
      </div>

      {/* Typing indicator */}
      {typingUsers.length > 0 && (
        <p className="text-xs text-gray-400 px-6 pb-1 bg-white">
          {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing…
        </p>
      )}

      {/* Input */}
      <div className="px-6 py-4 border-t border-gray-200 bg-white shrink-0">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={`Message #${channel?.name ?? '…'}`}
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


