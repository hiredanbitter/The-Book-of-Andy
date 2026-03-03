import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import './Header.css'

export function Header() {
  const { user, loading, signInWithGoogle, signOut } = useAuth()

  return (
    <header className="app-header">
      <div className="header-left">
        <Link to="/" className="header-logo">
          Podcast Transcript Search
        </Link>
      </div>
      <div className="header-right">
        {loading ? (
          <span className="auth-loading">Loading...</span>
        ) : user ? (
          <div className="user-menu">
            <Link to="/bookmarks" className="header-bookmarks-link">
              Bookmarks
            </Link>
            <span className="user-name">
              {user.user_metadata?.full_name ?? user.email ?? 'User'}
            </span>
            <button className="auth-button sign-out" onClick={signOut}>
              Sign Out
            </button>
          </div>
        ) : (
          <button className="auth-button sign-in" onClick={signInWithGoogle}>
            Sign In
          </button>
        )}
      </div>
    </header>
  )
}
