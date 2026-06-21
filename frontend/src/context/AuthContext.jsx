import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api/client'
import {
  SESSION_REVOKED_MESSAGE,
  SESSION_REVOKED_STORAGE_KEY,
} from '../constants/sessionMessages'

const AuthContext = createContext(null)

const TOKEN_KEY = 'crimetrack_token'
const USER_KEY = 'crimetrack_user'
const SESSION_POLL_MS = 10000

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState(() => {
    try {
      const raw = sessionStorage.getItem(USER_KEY)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  })
  const [loading, setLoading] = useState(!!sessionStorage.getItem(TOKEN_KEY))

  const persist = useCallback((nextToken, nextUser) => {
    setToken(nextToken)
    setUser(nextUser)
    if (nextToken) {
      sessionStorage.setItem(TOKEN_KEY, nextToken)
      sessionStorage.setItem(USER_KEY, JSON.stringify(nextUser))
      api.setAuthToken(nextToken)
    } else {
      sessionStorage.removeItem(TOKEN_KEY)
      sessionStorage.removeItem(USER_KEY)
      api.setAuthToken(null)
    }
  }, [])

  const handleSessionRevoked = useCallback(
    (message = SESSION_REVOKED_MESSAGE) => {
      sessionStorage.setItem(SESSION_REVOKED_STORAGE_KEY, message)
      persist(null, null)
      window.location.href = '/login?sesion=cerrada'
    },
    [persist]
  )

  useEffect(() => {
    if (token) api.setAuthToken(token)
  }, [token])

  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    api
      .authSessionStatus()
      .then((status) => {
        if (!status.valid) {
          handleSessionRevoked(
            status.message ||
              (status.code === 'SESSION_REVOKED' ? SESSION_REVOKED_MESSAGE : undefined)
          )
          return undefined
        }
        return api.authMe()
      })
      .then((data) => {
        if (!data) return
        setUser(data.user)
        sessionStorage.setItem(USER_KEY, JSON.stringify(data.user))
      })
      .catch((err) => {
        if (err.code === 'SESSION_REVOKED') {
          handleSessionRevoked(err.message)
          return
        }
        persist(null, null)
      })
      .finally(() => setLoading(false))
  }, [token, persist, handleSessionRevoked])

  const revokedRef = useRef(false)
  useEffect(() => {
    if (!token) return undefined
    revokedRef.current = false

    const check = async () => {
      try {
        const status = await api.authSessionStatus()
        if (!status.valid && !revokedRef.current) {
          revokedRef.current = true
          const msg =
            status.code === 'SESSION_REVOKED'
              ? status.message || SESSION_REVOKED_MESSAGE
              : status.message || SESSION_REVOKED_MESSAGE
          handleSessionRevoked(msg)
        }
      } catch (err) {
        if (err.code === 'SESSION_REVOKED' && !revokedRef.current) {
          revokedRef.current = true
          handleSessionRevoked(err.message)
        }
      }
    }

    check()
    const id = setInterval(check, SESSION_POLL_MS)
    return () => clearInterval(id)
  }, [token, handleSessionRevoked])

  const login = useCallback(
    async (email, password) => {
      const data = await api.authLogin(email, password)
      if (data.mfa_required) {
        return { mfaRequired: true, email: data.email, message: data.message }
      }
      persist(data.access_token, data.user)
      return { mfaRequired: false, user: data.user }
    },
    [persist]
  )

  const verifyMfa = useCallback(
    async (email, code) => {
      const data = await api.authVerifyMfa(email, code)
      persist(data.access_token, data.user)
      return data.user
    },
    [persist]
  )

  const resendMfa = useCallback((email) => api.authResendMfa(email), [])

  const logout = useCallback(async () => {
    try {
      if (token) await api.authLogout()
    } catch {
      /* ignore */
    }
    persist(null, null)
  }, [token, persist])

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      isAuthenticated: !!token && !!user,
      login,
      verifyMfa,
      resendMfa,
      logout,
    }),
    [token, user, loading, login, verifyMfa, resendMfa, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return ctx
}
