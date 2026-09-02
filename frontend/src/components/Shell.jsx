import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../store/auth'

export function Shell({ children }) {
  const { token, logout } = useAuth()
  const navigate = useNavigate()
  return (
    <div className="min-h-screen">
      <header className="border-b border-white/5">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="font-display text-lg font-semibold tracking-tight text-white">
            AI Teacher
          </Link>
          <nav className="flex items-center gap-6 text-sm text-white/70">
            {token ? (
              <>
                <Link to="/dashboard" className="hover:text-cyan-400 transition-colors">Dashboard</Link>
                <Link to="/progress" className="hover:text-cyan-400 transition-colors">Progress</Link>
                <button
                  onClick={() => { logout(); navigate('/') }}
                  className="hover:text-cyan-400 transition-colors"
                >
                  Sign out
                </button>
              </>
            ) : (
              <Link to="/auth" className="hover:text-cyan-400 transition-colors">Sign in</Link>
            )}
          </nav>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-6 py-10">{children}</main>
    </div>
  )
}
