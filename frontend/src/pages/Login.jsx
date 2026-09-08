import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../authContext'

function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { signIn } = useAuth()

  const doLogin = async (userAcc, passAcc) => {
    setError('')
    setMessage('')
    setLoading(true)
    try {
      const loggedUser = await signIn({ username: userAcc, password: passAcc })
      setMessage(`Login successful. Welcome ${loggedUser.username}.`)
      setTimeout(() => {
        if (loggedUser.is_admin || loggedUser.role === 'admin') {
          navigate('/admin')
        } else {
          navigate('/dashboard')
        }
      }, 300)
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid username or password.')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    doLogin(username, password)
  }

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/90 p-8 shadow-xl max-w-md mx-auto my-8 space-y-6">
      <h2 className="text-2xl font-bold text-white border-b border-slate-800 pb-4">Account Login</h2>

      {/* Quick 1-Click Login Shortcuts */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4 space-y-2">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">⚡ 1-Click Quick Demo Login:</p>
        <div className="grid grid-cols-3 gap-2">
          <button
            type="button"
            onClick={() => doLogin('donor_test', 'password123')}
            className="rounded-xl bg-slate-800 py-2 text-xs font-bold text-amber-300 hover:bg-amber-400 hover:text-slate-950 transition"
          >
            Donor
          </button>
          <button
            type="button"
            onClick={() => doLogin('ngo_test', 'password123')}
            className="rounded-xl bg-slate-800 py-2 text-xs font-bold text-emerald-300 hover:bg-emerald-400 hover:text-slate-950 transition"
          >
            NGO
          </button>
          <button
            type="button"
            onClick={() => doLogin('admin', 'admin123')}
            className="rounded-xl bg-slate-800 py-2 text-xs font-bold text-indigo-300 hover:bg-indigo-400 hover:text-slate-950 transition"
          >
            Admin
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block space-y-1.5 text-slate-300 text-sm font-semibold">
          Username
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-amber-400 focus:outline-none"
            placeholder="Username"
            required
          />
        </label>

        <label className="block space-y-1.5 text-slate-300 text-sm font-semibold">
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-amber-400 focus:outline-none"
            placeholder="••••••••"
            required
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-2xl bg-amber-400 py-3.5 text-sm font-bold text-slate-950 transition hover:bg-amber-300 disabled:opacity-60 shadow-md"
        >
          {loading ? 'Logging in…' : 'Login'}
        </button>
      </form>

      {message && <p className="rounded-2xl bg-emerald-500/15 p-3 text-xs text-emerald-200">{message}</p>}
      {error && <p className="rounded-2xl bg-rose-500/15 p-3 text-xs text-rose-200">{error}</p>}

      <p className="text-center text-xs text-slate-400 pt-2">
        Don't have an account?{' '}
        <Link to="/register" className="font-bold text-amber-300 hover:underline">
          Register
        </Link>
      </p>
    </div>
  )
}

export default Login
