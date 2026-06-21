import { Routes, Route } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import ChannelView from '../components/ChannelView'
import { useAuthStore } from '../store/auth'

function WelcomePanel() {
  const org = useAuthStore((s) => s.org)
  return (
    <div className="flex-1 flex flex-col items-center justify-center bg-gray-50 text-center px-8">
      <div className="text-5xl mb-4">💬</div>
      <h2 className="text-xl font-semibold text-gray-800 mb-2">
        Welcome to {org?.name ?? 'Crewchat'}
      </h2>
      <p className="text-sm text-gray-400 max-w-xs">
        Select a channel from the sidebar to start chatting with your team.
      </p>
    </div>
  )
}

export default function ChatPage() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 overflow-hidden">
        <Routes>
          <Route path="channels/:channelId" element={<ChannelView />} />
          <Route path="*" element={<WelcomePanel />} />
        </Routes>
      </div>
    </div>
  )
}
