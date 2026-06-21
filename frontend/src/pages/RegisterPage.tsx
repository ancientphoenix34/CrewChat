import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../api/client'
import { useAuthStore } from '../store/auth'
import Logo from '../components/Logo'

export default function RegisterPage() {
  const [orgName, setOrgName] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    try {
      const { data } = await api.post('/auth/register-org', {
        org_name: orgName,
        display_name: displayName,
        email,
        password,
      })
      setAuth(data.access_token, data.user, data.organization)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Registration failed')
    }
  }

  return (
    <div className="min-h-screen flex">

      {/* ── Left panel: branding ── */}
      <div className="hidden lg:flex flex-col w-1/2 bg-gradient-to-br from-purple-700 to-purple-900 text-white p-10">

        {/* Logo top-left */}
        <div className="flex items-center gap-3">
          <Logo size={40} />
          <span className="text-xl font-bold tracking-tight">Crewchat</span>
        </div>

        {/* Centred marketing copy */}
        <div className="flex-1 flex flex-col justify-center max-w-md">
          <h2 className="text-4xl font-bold leading-tight mb-4">
            Team chat,<br />reimagined.
          </h2>
          <p className="text-purple-200 text-lg leading-relaxed mb-8">
            Bring your crew together with real-time channels, direct messages,
            and live updates — all in one place.
          </p>

          {/* Feature bullets */}
          <ul className="space-y-3 text-purple-100">
            {[
              '⚡  Real-time messaging with WebSockets',
              '🔒  Private channels and direct messages',
              '🏢  Multi-workspace support',
              '📨  Invite your team in seconds',
            ].map(f => (
              <li key={f} className="flex items-center gap-2 text-sm">{f}</li>
            ))}
          </ul>
        </div>

        <p className="text-purple-300 text-xs">© 2026 Crewchat</p>
      </div>

      {/* ── Right panel: form ── */}
      <div className="flex-1 flex flex-col justify-center items-center bg-gray-50 p-8">

        {/* Mobile logo (only visible on small screens) */}
        <div className="flex items-center gap-2 mb-8 lg:hidden">
          <Logo size={32} />
          <span className="text-lg font-bold text-gray-900">Crewchat</span>
        </div>

        <div className="bg-white rounded-2xl shadow-md w-full max-w-sm p-8">
          <h1 className="text-2xl font-semibold text-gray-900 mb-1">Create your workspace</h1>
          <p className="text-sm text-gray-500 mb-6">Get your team up and running in minutes.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              placeholder="Organisation name"
              value={orgName}
              onChange={e => setOrgName(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-purple-400"
            />
            <input
              placeholder="Your name"
              value={displayName}
              onChange={e => setDisplayName(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-purple-400"
            />
            <input
              placeholder="Email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-purple-400"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-purple-400"
            />
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <button
              type="submit"
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg py-2.5 text-sm transition-colors"
            >
              Create workspace
            </button>
          </form>

          <p className="text-sm text-gray-500 mt-4 text-center">
            Already have an account?{' '}
            <Link to="/login" className="text-purple-600 hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>

    </div>
  )
}
