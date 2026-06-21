import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api from '../api/client'
import { useAuthStore } from '../store/auth'
import Logo from './Logo'

interface Channel {
  id: string
  name: string
  description: string | null
  is_private: boolean
}

export default function Sidebar() {
  const [channels, setChannels] = useState<Channel[]>([])
  const [adding, setAdding] = useState(false)
  const [newName, setNewName] = useState('')
  const { channelId } = useParams()
  const navigate = useNavigate()
  const { user, org, logout } = useAuthStore()

  async function loadChannels() {
    const { data } = await api.get('/channels')
    setChannels(data.channels)
  }

  useEffect(() => { loadChannels() }, [])

  async function handleAddChannel(e: React.FormEvent) {
    e.preventDefault()
    if (!newName.trim()) return
    await api.post('/channels', { name: newName.trim() })
    setNewName('')
    setAdding(false)
    loadChannels()
  }

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="w-64 min-h-screen bg-gray-900 text-gray-300 flex flex-col shrink-0">

      {/* Org header */}
      <div className="px-4 py-4 border-b border-gray-700 flex items-center gap-2">
        <Logo size={28} />
        <span className="font-semibold text-white truncate">{org?.name ?? 'Crewchat'}</span>
      </div>

      {/* Channels section */}
      <div className="flex-1 overflow-y-auto py-4">
        <div className="px-4 mb-1 flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Channels</span>
          <button
            onClick={() => setAdding(true)}
            className="text-gray-500 hover:text-white text-lg leading-none"
            title="Add channel"
          >
            +
          </button>
        </div>

        {/* Add channel input */}
        {adding && (
          <form onSubmit={handleAddChannel} className="px-3 mb-2">
            <input
              autoFocus
              placeholder="channel-name"
              value={newName}
              onChange={e => setNewName(e.target.value)}
              onKeyDown={e => e.key === 'Escape' && setAdding(false)}
              className="w-full bg-gray-800 text-white text-sm rounded px-2 py-1.5 outline-none border border-purple-500"
            />
          </form>
        )}

        {/* Channel list */}
        <ul>
          {channels.map(ch => (
            <li key={ch.id}>
              <button
                onClick={() => navigate(`/channels/${ch.id}`)}
                className={`w-full text-left px-4 py-1.5 text-sm rounded-md mx-1 flex items-center gap-1.5 transition-colors ${
                  channelId === ch.id
                    ? 'bg-purple-700 text-white'
                    : 'hover:bg-gray-800 text-gray-400 hover:text-white'
                }`}
              >
                <span className="text-gray-500">#</span>
                <span className="truncate">{ch.name}</span>
              </button>
            </li>
          ))}
        </ul>

        {/* DMs section */}
        <div className="px-4 mt-6 mb-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Direct Messages</span>
        </div>
        <p className="px-4 text-xs text-gray-600 italic">Coming soon</p>
      </div>

      {/* User footer */}
      <div className="px-4 py-3 border-t border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-7 h-7 rounded-full bg-purple-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
            {user?.display_name?.[0]?.toUpperCase() ?? '?'}
          </div>
          <span className="text-sm text-gray-300 truncate">{user?.display_name}</span>
        </div>
        <button
          onClick={handleLogout}
          className="text-xs text-gray-500 hover:text-red-400 transition-colors ml-2 shrink-0"
        >
          Logout
        </button>
      </div>

    </div>
  )
}
