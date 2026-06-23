import { useEffect, useState } from 'react'
import { useNavigate, useParams, useLocation } from 'react-router-dom'
import api from '../api/client'
import { useAuthStore } from '../store/auth'
import Logo from './Logo'
import InviteModal from './InviteModal'
import ConfirmDialog from './ConfirmDialog'

interface Channel {
  id: string
  name: string
}

interface Member {
  id: string
  email: string
  display_name: string
}

export default function Sidebar() {
  const [channels, setChannels] = useState<Channel[]>([])
  const [members, setMembers] = useState<Member[]>([])
  const [adding, setAdding] = useState(false)
  const [newName, setNewName] = useState('')
  const { channelId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const { user, org, logout } = useAuthStore()
  const [showInvite, setShowInvite] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)

  async function loadChannels() {
    const { data } = await api.get('/channels')
    setChannels(data.channels)
  }

  async function loadMembers() {
    const { data } = await api.get('/auth/members')
    setMembers(data)
  }

  useEffect(() => {
    loadChannels()
    loadMembers()
  }, [])

  function sanitizeChannelName(value: string) {
    return value
      .toLowerCase()
      .replace(/\s+/g, '-')       // spaces → hyphens
      .replace(/[^a-z0-9-]/g, '') // strip anything else
      .slice(0, 25)               // max 25 chars
  }

  async function handleAddChannel(e: React.FormEvent) {
    e.preventDefault()
    const name = sanitizeChannelName(newName)
    if (!name) return
    await api.post('/channels', { name })
    setNewName('')
    setAdding(false)
    loadChannels()
  }

  async function handleOpenDM(member: Member) {
    const { data } = await api.post(`/dms/${member.id}`)
    navigate(`/dms/${data.id}`, { state: { displayName: member.display_name } })
  }

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const activeDmId = location.pathname.startsWith('/dms/')
    ? location.pathname.split('/dms/')[1]
    : null

  return (
    <div className="w-64 min-h-screen bg-gray-900 text-gray-300 flex flex-col shrink-0">

      {/* Org header */}
      <div className="px-4 py-4 border-b border-gray-700 flex items-center gap-2">
        <Logo size={28} />
        <span className="font-semibold text-white truncate">{org?.name ?? 'Crewchat'}</span>
      </div>

      <div className="flex-1 overflow-y-auto py-4 sidebar-scroll">

        {/* Channels */}
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

        {adding && (
          <form onSubmit={handleAddChannel} className="px-3 mb-2">
            <input
              autoFocus
              placeholder="channel-name"
              value={newName}
              onChange={e => setNewName(sanitizeChannelName(e.target.value))}
              onKeyDown={e => e.key === 'Escape' && setAdding(false)}
              className="w-full bg-gray-800 text-white text-sm rounded px-2 py-1.5 outline-none border border-purple-500"
            />
          </form>
        )}

        <ul className="mb-4">
          {channels.map(ch => (
            <li key={ch.id}>
              <button
                onClick={() => navigate(`/channels/${ch.id}`)}
                className={`w-full text-left px-4 py-1.5 text-sm rounded-md mx-1 flex items-center gap-1.5 transition-colors ${channelId === ch.id
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

        {/* Direct Messages */}
        <div className="px-4 mb-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Direct Messages</span>
        </div>

        <ul>
          {members.map(m => (
            <li key={m.id}>
              <button
                onClick={() => handleOpenDM(m)}
                className={`w-full text-left px-4 py-1.5 text-sm rounded-md mx-1 flex items-center gap-2 transition-colors ${activeDmId === m.id
                  ? 'bg-purple-700 text-white'
                  : 'hover:bg-gray-800 text-gray-400 hover:text-white'
                  }`}
              >
                <div className="w-5 h-5 rounded-full bg-gray-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
                  {m.display_name[0]?.toUpperCase()}
                </div>
                <span className="truncate">{m.display_name}</span>
              </button>
            </li>
          ))}
          {members.length === 0 && (
            <p className="px-4 text-xs text-gray-600 italic">No other members yet</p>
          )}
        </ul>
      </div>

      {/* User footer */}
      <div className="px-4 py-3 border-t border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-7 h-7 rounded-full bg-purple-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
              {user?.display_name?.[0]?.toUpperCase() ?? '?'}
            </div>
            <span className="text-sm text-gray-300 truncate">{user?.display_name}</span>
          </div>
          <button
            onClick={() => setShowLogoutConfirm(true)}
            className="text-xs text-gray-500 hover:text-red-400 transition-colors ml-2 shrink-0"
          >
            Logout
          </button>
        </div>
        <button
          onClick={() => setShowInvite(true)}
          className="w-full text-xs text-purple-400 hover:text-purple-300 text-left transition-colors"
        >
          + Invite teammates
        </button>
      </div>

      {showInvite && <InviteModal onClose={() => setShowInvite(false)} />}

      {showLogoutConfirm && (
        <ConfirmDialog
          title="Sign out"
          message="Are you sure you want to logout?"
          mode="danger"
          confirmLabel="Logout"
          onConfirm={handleLogout}
          onCancel={() => setShowLogoutConfirm(false)}
        />
      )}
    </div>

  )
}
