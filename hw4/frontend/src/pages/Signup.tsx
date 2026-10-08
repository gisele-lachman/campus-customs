import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { Monogram } from '../components/Graphics'
import type { SignupDetails } from '../auth/authApi'

const MIN_PASSWORD_LENGTH = 8 // keep in sync with backend/users.py
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

const FIELDS: { key: keyof SignupDetails; label: string; type: string; autoComplete: string }[] = [
  { key: 'first_name', label: 'First name', type: 'text', autoComplete: 'given-name' },
  { key: 'last_name', label: 'Last name', type: 'text', autoComplete: 'family-name' },
  { key: 'email', label: 'Email', type: 'email', autoComplete: 'email' },
  { key: 'password', label: 'Password', type: 'password', autoComplete: 'new-password' },
  { key: 'confirm_password', label: 'Confirm password', type: 'password', autoComplete: 'new-password' },
]

// Quick checks in the browser for friendlier messages. The backend checks again.
function validate(d: SignupDetails): string | null {
  if (Object.values(d).some((v) => !v.trim())) return 'Please fill in every field.'
  if (!EMAIL_RE.test(d.email.trim())) return 'That doesn’t look like an email address.'
  if (d.password.length < MIN_PASSWORD_LENGTH)
    return `Your password must be at least ${MIN_PASSWORD_LENGTH} characters.`
  if (d.password !== d.confirm_password) return 'The passwords don’t match.'
  return null
}

export default function Signup() {
  const { user, signup } = useAuth()
  const navigate = useNavigate()
  const [details, setDetails] = useState<SignupDetails>({
    first_name: '', last_name: '', email: '', password: '', confirm_password: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const problem = validate(details)
    if (problem) {
      setError(problem)
      return
    }
    setBusy(true)
    setError(null)
    try {
      await signup(details)
      navigate('/')
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="auth-card-head">
          <Monogram size={54} />
          <h1>Join the roster</h1>
          <p>Create an account and we’ll remember your chat</p>
        </div>
        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          {error && <p className="form-error" role="alert">{error}</p>}
          {[FIELDS.slice(0, 2), ...FIELDS.slice(2).map((f) => [f])].map((group) => (
            <div key={group[0].key} className={group.length > 1 ? 'row' : undefined}>
              {group.map((f) => (
                <label key={f.key}>
                  {f.label}
                  <input
                    name={f.key}
                    type={f.type}
                    autoComplete={f.autoComplete}
                    value={details[f.key]}
                    onChange={(e) => setDetails({ ...details, [f.key]: e.target.value })}
                  />
                </label>
              ))}
            </div>
          ))}
          <p className="muted small">At least {MIN_PASSWORD_LENGTH} characters.</p>
          <button type="submit" className="button" disabled={busy}>
            {busy ? 'Creating account…' : 'Create account'}
          </button>
          <p className="muted switch">
            Already have an account? <Link to="/login">Log in</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
