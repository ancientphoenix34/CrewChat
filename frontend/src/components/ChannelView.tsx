import { useEffect, useRef, useState } from 'react'
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

const WS_BASE = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000')
  .replace(/^http/, 'ws')

export default function ChannelView() {
  const { channelId } = useParams<{ channelId: string }>()
  const [channel, setChannel] = useState<Channel | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const token = useAuthStore((s) => s.token)
  const currentUserId = useAuthStore((s) => s.user?.id)

  // Load channel info + message history
  useEffect(() => {
    if (!channelId) return
    setMessages([])
    setChannel(null)

    api.get(`/channels/${channelId}`).then(r => setChannel(r.data))
    api.get(`/channels/${channelId}/messages`).then(r =>
      setMessages(r.data.messages)
    )
  }, [channelId])

  // WebSocket — opens on mount, closes on unmount or channel switch
  useEffect(() => {
    if (!channelId || !token) return
    const ws = new WebSocket(`${WS_BASE}/channels/${channelId}/ws?token=${token}`)
    ws.onmessage = (e) => {
      const msg: Message = JSON.parse(e.data)
      setMessages(prev => [...prev, msg])
    }
    return () => ws.close()
  }, [channelId, token])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim() || sending || !channelId) return
    setSending(true)
    try {
      await api.post(`/channels/${channelId}/messages`, { content: input.trim() })
      setInput('')
      // Do NOT push message here — the WS echo will deliver it
    } finally {
      setSending(false)
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
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3 bg-white">
        {messages.length === 0 && (
          <p className="text-sm text-gray-400 text-center mt-10">
            No messages yet. Say hello!
          </p>
        )}
        {messages.map(msg => {
          const isOwn = msg.sender_id === currentUserId
          return (
            <div key={msg.id} className="flex items-start gap-3 group">
              {/* Avatar */}
              <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-700 text-xs font-bold shrink-0 mt-0.5">
                {msg.sender_id.slice(0, 2).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                  <span className={`text-sm font-semibold ${isOwn ? 'text-purple-700' : 'text-gray-800'}`}>
                    {isOwn ? 'You' : msg.sender_id.slice(0, 8)}
                  </span>
                  <span className="text-xs text-gray-400">{formatTime(msg.created_at)}</span>
                </div>
                <p className="text-sm text-gray-700 break-words">{msg.content}</p>
              </div>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-gray-200 bg-white shrink-0">
        <form onSubmit={handleSend} className="flex gap-3">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
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
