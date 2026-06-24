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
  unread_count: number
}

interface DMConversation {
  id: string
  other_user_id: string
  other_user_name: string
  unread_count: number
}

interface Member {
  id: string
  email: string
  display_name: string
}

export default function Sidebar() {
  const [channels, setChannels] = useState<Channel[]>([])
  const [conversations, setConversations] = useState<DMConversation[]>([])
  const [members, setMembers] = useState<Member[]>([])
  const [adding, setAdding] = useState(false)
  const [newName, setNewName] = useState('')
  const [showNewDM, setShowNewDM] = useState(false)
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

  async function loadConversations() {
    const { data } = await api.get('/dms')
    setConversations(data.conversations)
  }

  async function loadMembers() {
    const { data } = await api.get('/auth/members')
    setMembers(data)
  }

  useEffect(() => {
    loadChannels()
    loadConversations()
    loadMembers()

    const onFocus = () => { loadChannels(); loadConversations() }
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [])

  function sanitizeChannelName(value: string) {
    return value
      .toLowerCase()
      .replace(/\s+/g, '-')
      .replace(/[^a-z0-9-]/g, '')
      .slice(0, 25)
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
    setShowNewDM(false)
    const { data } = await api.post(`/dms/${member.id}`)
    navigate(`/dms/${data.id}`, { state: { displayName: member.display_name } })
    await loadConversations()
  }

  function handleClickChannel(ch: Channel) {
    setChannels(prev => prev.map(c => c.id === ch.id ? { ...c, unread_count: 0 } : c))
    navigate(`/channels/${ch.id}`)
  }

  function handleClickConversation(conv: DMConversation) {
    setConversations(prev => prev.map(c => c.id === conv.id ? { ...c, unread_count: 0 } : c))
    navigate(`/dms/${conv.id}`, { state: { displayName: conv.other_user_name } })
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
                onClick={() => handleClickChannel(ch)}
                className={`w-full text-left px-4 py-1.5 text-sm rounded-md mx-1 flex items-center gap-1.5 transition-colors ${channelId === ch.id
                  ? 'bg-purple-700 text-white'
                  : 'hover:bg-gray-800 text-gray-400 hover:text-white'
                }`}
              >
                <span className="text-gray-500">#</span>
                <span className="truncate flex-1">{ch.name}</span>
                {ch.unread_count > 0 && (
                  <span className="bg-purple-500 text-white text-xs font-bold rounded-full px-1.5 py-0.5 min-w-[18px] text-center leading-none">
                    {ch.unread_count > 99 ? '99+' : ch.unread_count}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>

        {/* Direct Messages */}
        <div className="px-4 mb-1 flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Direct Messages</span>
          <button
            onClick={() => setShowNewDM(v => !v)}
            className="text-gray-500 hover:text-white text-lg leading-none"
            title="New DM"
          >
            +
          </button>
        </div>

        {showNewDM && (
          <div className="mx-3 mb-2 bg-gray-800 rounded-md border border-gray-700 overflow-hidden">
            {members.length === 0
              ? <p className="px-3 py-2 text-xs text-gray-500 italic">No other members yet</p>
              : members.map(m => (
                <button
                  key={m.id}
                  onClick={() => handleOpenDM(m)}
                  className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 flex items-center gap-2"
                >
                  <div className="w-5 h-5 rounded-full bg-gray-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
                    {m.display_name[0]?.toUpperCase()}
                  </div>
                  <span className="truncate">{m.display_name}</span>
                </button>
              ))
            }
          </div>
        )}

        <ul>
          {conversations.map(conv => (
            <li key={conv.id}>
              <button
                onClick={() => handleClickConversation(conv)}
                className={`w-full text-left px-4 py-1.5 text-sm rounded-md mx-1 flex items-center gap-2 transition-colors ${activeDmId === conv.id
                  ? 'bg-purple-700 text-white'
                  : 'hover:bg-gray-800 text-gray-400 hover:text-white'
                }`}
              >
                <div className="w-5 h-5 rounded-full bg-gray-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
                  {conv.other_user_name[0]?.toUpperCase()}
                </div>
                <span className="truncate flex-1">{conv.other_user_name}</span>
                {conv.unread_count > 0 && (
                  <span className="bg-purple-500 text-white text-xs font-bold rounded-full px-1.5 py-0.5 min-w-[18px] text-center leading-none">
                    {conv.unread_count > 99 ? '99+' : conv.unread_count}
                  </span>
                )}
              </button>
            </li>
          ))}
          {conversations.length === 0 && !showNewDM && (
            <p className="px-4 text-xs text-gray-600 italic">No conversations yet</p>
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
