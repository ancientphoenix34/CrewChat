import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../api/client'
import { useAuthStore } from '../store/auth'
import Logo from '../components/Logo'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    try {
      const { data } = await api.post('/auth/login', { email, password })
      setAuth(data.access_token, data.user, data.organization)
      navigate('/')
    } catch {
      setError('Invalid email or password')
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
            Welcome<br />back.
          </h2>
          <p className="text-purple-200 text-lg leading-relaxed mb-8">
            Your team is waiting. Jump back into your channels,
            messages, and conversations right where you left off.
          </p>

          {/* Stats / social proof */}
          <div className="grid grid-cols-2 gap-4">
            {[
              { value: 'Real-time', label: 'WebSocket delivery' },
              { value: 'Private', label: 'Encrypted channels' },
              { value: 'Fast', label: 'Built on FastAPI' },
              { value: 'Simple', label: 'No bloat' },
            ].map(s => (
              <div key={s.label} className="bg-white/10 rounded-xl p-4">
                <p className="text-white font-semibold text-lg">{s.value}</p>
                <p className="text-purple-200 text-xs mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="text-purple-300 text-xs">© 2026 Crewchat</p>
      </div>

      {/* ── Right panel: form ── */}
      <div className="flex-1 flex flex-col justify-center items-center bg-gray-50 p-8">

        {/* Mobile logo */}
        <div className="flex items-center gap-2 mb-8 lg:hidden">
          <Logo size={32} />
          <span className="text-lg font-bold text-gray-900">Crewchat</span>
        </div>

        <div className="bg-white rounded-2xl shadow-md w-full max-w-sm p-8">
          <h1 className="text-2xl font-semibold text-gray-900 mb-1">Sign in</h1>
          <p className="text-sm text-gray-500 mb-6">Enter your credentials to access your workspace.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
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
              Sign in
            </button>
          </form>

          <p className="text-sm text-gray-500 mt-4 text-center">
            No account?{' '}
            <Link to="/register" className="text-purple-600 hover:underline">
              Create a workspace
            </Link>
          </p>
        </div>
      </div>

    </div>
  )
}
