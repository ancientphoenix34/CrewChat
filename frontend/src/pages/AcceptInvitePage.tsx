import { useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import api from '../api/client'
import { useAuthStore } from '../store/auth'
import Logo from '../components/Logo'

export default function AcceptInvitePage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post('/auth/accept-invite', {
        token,
        display_name: displayName,
        password,
      })
      setAuth(data.access_token, data.user, data.organization)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Invalid or expired invitation')
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-gray-500 mb-4">No invite token found in the link.</p>
          <Link to="/login" className="text-purple-600 hover:underline text-sm">Go to login</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex">

      {/* Left branding panel */}
      <div className="hidden lg:flex flex-col w-1/2 bg-gradient-to-br from-purple-700 to-purple-900 text-white p-10">
        <div className="flex items-center gap-3">
          <Logo size={40} />
          <span className="text-xl font-bold tracking-tight">Crewchat</span>
        </div>
        <div className="flex-1 flex flex-col justify-center max-w-md">
          <h2 className="text-4xl font-bold leading-tight mb-4">
            You've been<br />invited!
          </h2>
          <p className="text-purple-200 text-lg leading-relaxed">
            Create your account to join the workspace and start chatting with your team.
          </p>
        </div>
        <p className="text-purple-300 text-xs">© 2026 Crewchat</p>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex flex-col justify-center items-center bg-gray-50 p-8">
        <div className="lg:hidden flex items-center gap-2 mb-8">
          <Logo size={32} />
          <span className="text-lg font-bold text-gray-900">Crewchat</span>
        </div>

        <div className="bg-white rounded-2xl shadow-md w-full max-w-sm p-8">
          <h1 className="text-2xl font-semibold text-gray-900 mb-1">Create your account</h1>
          <p className="text-sm text-gray-500 mb-6">Choose a name and password to get started.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              placeholder="Your name"
              value={displayName}
              onChange={e => setDisplayName(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-purple-400"
            />
            <input
              type="password"
              placeholder="Password (min 8 characters)"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-purple-400"
            />
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <button
              type="submit"
              disabled={loading || !displayName.trim() || !password}
              className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-40 text-white font-medium rounded-lg py-2.5 text-sm transition-colors"
            >
              {loading ? 'Joining…' : 'Join workspace'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
