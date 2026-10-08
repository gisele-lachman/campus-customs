import { useEffect, useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { displayFirstName, useAuth } from '../auth/AuthContext'
import { Monogram } from './Graphics'

const links = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

export default function NavBar() {
  const { user, loading, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  // Close the phone menu whenever the page changes.
  useEffect(() => {
    setMenuOpen(false)
  }, [location.pathname])

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <>
      <div className="topline">
        Vintage varsity gear<span className="hide-sm"> <span>·</span> Residential colleges</span> <span>·</span> Bulldog pride
      </div>
      <header className="navbar">
        <NavLink to="/" className="brand" aria-label="Campus Customs home">
          <Monogram />
          <span>
            <span className="brand-name">Campus Customs</span>
            <span className="brand-tag">Yale gear with a varsity heart</span>
          </span>
        </NavLink>
        <button
          type="button"
          className="nav-toggle"
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((o) => !o)}
        >
          {menuOpen ? '×' : '☰'}
        </button>
        <nav className={`nav-links${menuOpen ? ' open' : ''}`}>
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end}>
              {link.label}
            </NavLink>
          ))}
          {!loading && user && (
            <>
              <span className="nav-greeting">Hi, {displayFirstName(user)}!</span>
              <button type="button" className="nav-button outline" onClick={handleLogout}>
                Log out
              </button>
            </>
          )}
          {!loading && !user && (
            <>
              <NavLink to="/login">Log in</NavLink>
              <NavLink to="/signup" className="nav-cta">
                Create account
              </NavLink>
            </>
          )}
        </nav>
      </header>
    </>
  )
}
