import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { registerUser } from '../api'

function Register() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('donor')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)

    try {
      await registerUser({ username, email, password, phone: phone || undefined, role })
      setMessage('Account registered successfully! Redirecting to login...')
      setTimeout(() => navigate('/login'), 1200)
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to register account.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto rounded-3xl border border-slate-800 bg-slate-900/90 p-8 shadow-xl my-8">
      <h2 className="text-2xl font-bold text-white border-b border-slate-800 pb-4">Register Account</h2>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <label className="block space-y-1.5 text-slate-300 text-sm font-semibold">
          Role
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 font-bold focus:border-amber-400 focus:outline-none"
          >
            <option value="donor">Donor (Individual / Restaurant / Hotel)</option>
            <option value="ngo">NGO Representative</option>
            <option value="admin">Administrator</option>
          </select>
        </label>

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
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-amber-400 focus:outline-none"
            placeholder="Email address"
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

        <label className="block space-y-1.5 text-slate-300 text-sm font-semibold">
          Phone Number
          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-amber-400 focus:outline-none"
            placeholder="Phone number"
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-2xl bg-amber-400 py-3.5 text-sm font-bold text-slate-950 transition hover:bg-amber-300 disabled:opacity-60 shadow-md"
        >
          {loading ? 'Creating Account…' : 'Register Account'}
        </button>
      </form>

      {message && <p className="mt-4 rounded-2xl bg-emerald-500/15 p-3 text-xs text-emerald-200">{message}</p>}
      {error && <p className="mt-4 rounded-2xl bg-rose-500/15 p-3 text-xs text-rose-200">{error}</p>}

      <p className="mt-6 text-center text-xs text-slate-400">
        Already have an account?{' '}
        <Link to="/login" className="font-bold text-amber-300 hover:underline">
          Login
        </Link>
      </p>
    </div>
  )
}

export default Register
