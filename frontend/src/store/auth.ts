import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  display_name: string
}

interface Org {
  id: string
  name: string
}

interface AuthState {
  token: string | null
  user: User | null
  org: Org | null
  setAuth: (token: string, user: User, org: Org) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      org: null,
      setAuth: (token, user, org) => set({ token, user, org }),
      logout: () => set({ token: null, user: null, org: null }),
    }),
    { name: 'crewchat-auth' }
  )
)
