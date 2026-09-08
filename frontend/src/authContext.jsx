import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { clearToken, getToken, setToken } from './auth'
import { getMe, login } from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }

    getMe()
      .then((currentUser) => setUser(currentUser))
      .catch(() => {
        clearToken()
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const signIn = async (credentials) => {
    const result = await login(credentials)
    setToken(result.access_token)
    const currentUser = await getMe()
    setUser(currentUser)
    return currentUser
  }

  const signOut = () => {
    clearToken()
    setUser(null)
  }

  const value = useMemo(
    () => ({
      user,
      loading,
      error,
      signIn,
      signOut,
      isAuthenticated: Boolean(user),
    }),
    [user, loading, error]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
