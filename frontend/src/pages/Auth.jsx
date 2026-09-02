import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shell } from '../components/Shell'
import { useAuth } from '../store/auth'

export default function Auth() {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const { login, register, loading, error } = useAuth()
  const navigate = useNavigate()

  async function submit(e) {
    e.preventDefault()
    const ok = mode === 'login' ? await login(email, password) : await register(email, password, fullName)
    if (ok) navigate('/dashboard')
  }

  return (
    <Shell>
      <div className="max-w-sm mx-auto glass rounded-2xl p-8 mt-8">
        <div className="flex gap-2 mb-6 text-sm">
          <button
            onClick={() => setMode('login')}
            className={`flex-1 py-2 rounded-lg transition-colors ${mode === 'login' ? 'bg-cyan-500 text-navy-950 font-medium' : 'text-white/60'}`}
          >
            Sign in
          </button>
          <button
            onClick={() => setMode('register')}
            className={`flex-1 py-2 rounded-lg transition-colors ${mode === 'register' ? 'bg-cyan-500 text-navy-950 font-medium' : 'text-white/60'}`}
          >
            Create account
          </button>
        </div>
        <form onSubmit={submit} className="space-y-4">
          {mode === 'register' && (
            <input
              placeholder="Full name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full bg-navy-900/70 border border-white/10 rounded-lg px-3 py-2.5 text-sm outline-none focus:border-cyan-400"
            />
          )}
          <input
            type="email"
            required
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-navy-900/70 border border-white/10 rounded-lg px-3 py-2.5 text-sm outline-none focus:border-cyan-400"
          />
          <input
            type="password"
            required
            minLength={8}
            placeholder="Password (min 8 characters)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-navy-900/70 border border-white/10 rounded-lg px-3 py-2.5 text-sm outline-none focus:border-cyan-400"
          />
          {error && <p className="text-red-400 text-xs">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-cyan-500 text-navy-950 font-medium hover:bg-cyan-400 transition-colors disabled:opacity-50"
          >
            {loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>
      </div>
    </Shell>
  )
}
