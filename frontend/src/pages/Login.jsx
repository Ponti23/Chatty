import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { setToken } from '../api'

export default function Login() {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [tenantName, setTenantName] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    let res
    if (mode === 'register') {
      res = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, tenant_name: tenantName }),
      })
    } else {
      const form = new URLSearchParams({ username: email, password })
      res = await fetch('/api/v1/auth/login', { method: 'POST', body: form })
    }

    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      setError(body.detail || 'Authentication failed')
      return
    }

    const { access_token } = await res.json()
    setToken(access_token)
    navigate('/chat')
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="bg-white shadow rounded-lg p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-6 text-center">Chatbot Platform</h1>

        <div className="flex mb-6 border rounded overflow-hidden">
          <button
            className={`flex-1 py-2 text-sm font-medium ${mode === 'login' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600'}`}
            onClick={() => setMode('login')}
          >
            Sign In
          </button>
          <button
            className={`flex-1 py-2 text-sm font-medium ${mode === 'register' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600'}`}
            onClick={() => setMode('register')}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <input
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              placeholder="Company name"
              value={tenantName}
              onChange={(e) => setTenantName(e.target.value)}
              required
            />
          )}
          <input
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button
            type="submit"
            className="w-full bg-indigo-600 text-white rounded py-2 text-sm font-medium hover:bg-indigo-700"
          >
            {mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  )
}
