// Calls to the backend's /api/auth routes. The login cookie is HttpOnly, so the
// browser sends it automatically and this code never sees or stores it.

export interface User {
  id: number
  name: string
  email: string
  first_name: string | null
  last_name: string | null
  created_at: string
}

export interface SignupDetails {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

async function post<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : 'Something went wrong. Please try again.'
    throw new Error(detail)
  }
  return data as T
}

export const signup = (details: SignupDetails) => post<User>('/api/auth/signup', details)
export const login = (email: string, password: string) => post<User>('/api/auth/login', { email, password })
export const logout = () => post<{ ok: boolean }>('/api/auth/logout')

export async function fetchCurrentUser(): Promise<User | null> {
  const res = await fetch('/api/auth/me')
  return res.ok ? ((await res.json()) as User | null) : null
}
