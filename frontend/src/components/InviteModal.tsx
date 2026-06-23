import { useState } from 'react'
import api from '../api/client'

interface Props {
  onClose: () => void
}

export default function InviteModal({ onClose }: Props) {
  const [email, setEmail] = useState('')
  const [inviteLink, setInviteLink] = useState('')
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!email.trim()) return
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post('/auth/invite', { email: email.trim() })
      const link = `${window.location.origin}/accept-invite?token=${data.token}`
      setInviteLink(link)
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Failed to create invite')
    } finally {
      setLoading(false)
    }
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(inviteLink)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      {/* Modal card */}
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 mx-4"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Invite a teammate</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        {!inviteLink ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              autoFocus
              type="email"
              placeholder="teammate@company.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-purple-400"
            />
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <button
              type="submit"
              disabled={loading || !email.trim()}
              className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-40 text-white font-medium rounded-lg py-2.5 text-sm transition-colors"
            >
              {loading ? 'Creating invite…' : 'Generate invite link'}
            </button>
          </form>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              Share this link with <span className="font-medium">{email}</span>. It expires in 7 days.
            </p>
            <div className="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700 break-all border border-gray-200">
              {inviteLink}
            </div>
            <button
              onClick={handleCopy}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg py-2.5 text-sm transition-colors"
            >
              {copied ? '✓ Copied!' : 'Copy link'}
            </button>
            <button
              onClick={() => { setInviteLink(''); setEmail('') }}
              className="w-full text-sm text-gray-500 hover:text-gray-700"
            >
              Invite another person
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
