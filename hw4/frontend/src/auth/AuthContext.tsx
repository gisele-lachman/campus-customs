import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import * as authApi from './authApi'
import type { SignupDetails, User } from './authApi'

interface AuthState {
  user: User | null
  loading: boolean // true until we've asked the backend who is logged in
  login: (email: string, password: string) => Promise<void>
  signup: (details: SignupDetails) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // On page load (including refresh), ask the backend if our cookie is still valid.
  useEffect(() => {
    authApi.fetchCurrentUser().then(setUser).finally(() => setLoading(false))
  }, [])

  const value: AuthState = {
    user,
    loading,
    login: async (email, password) => setUser(await authApi.login(email, password)),
    signup: async (details) => setUser(await authApi.signup(details)),
    logout: async () => {
      await authApi.logout()
      setUser(null)
    },
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}

export const displayFirstName = (user: User) => user.first_name || user.name.split(' ')[0]
