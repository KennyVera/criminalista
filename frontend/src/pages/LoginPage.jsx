import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { Shield, LogIn, AlertCircle } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { Button, Card, PasswordInput } from '../components/ui'
import { useAppConfig } from '../context/AppConfigContext'
import {
  SESSION_REVOKED_MESSAGE,
  SESSION_REVOKED_STORAGE_KEY,
} from '../constants/sessionMessages'

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [email, setEmail] = useState('kennyvera43@gmail.com')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [sessionNotice, setSessionNotice] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const { appName, subtitle, iconUrl } = useAppConfig()

  useEffect(() => {
    if (searchParams.get('sesion') === 'cerrada') {
      const stored = sessionStorage.getItem(SESSION_REVOKED_STORAGE_KEY)
      setSessionNotice(stored || SESSION_REVOKED_MESSAGE)
      sessionStorage.removeItem(SESSION_REVOKED_STORAGE_KEY)
    }
  }, [searchParams])

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email.trim(), password)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message || 'No se pudo iniciar sesión')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 via-brand-50/30 to-slate-100 p-6">
      <Card className="w-full max-w-md shadow-xl">
        <div className="mb-6 flex items-center gap-3">
          {iconUrl ? (
            <img
              src={iconUrl}
              alt={appName}
              className="h-12 w-12 shrink-0 rounded-xl object-cover"
            />
          ) : (
            <div className="rounded-xl bg-brand-600 p-3 text-white">
              <Shield className="h-8 w-8" />
            </div>
          )}
          <div>
            <h1 className="text-xl font-bold text-slate-900">{appName}</h1>
            <p className="text-sm text-slate-500">
              {subtitle || 'Autenticación y Seguridad (RBAC)'}
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700">Correo</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
              required
              autoComplete="username"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700">Contraseña</span>
            <PasswordInput
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </label>

          {sessionNotice && (
            <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <p>{sessionNotice}</p>
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <p>{error}</p>
            </div>
          )}

          <div className="flex justify-end">
            <Link
              to="/recuperar-contrasena"
              className="text-sm text-brand-600 hover:text-brand-700 hover:underline"
            >
              ¿Olvidaste tu contraseña?
            </Link>
          </div>

          <Button type="submit" className="w-full justify-center" disabled={submitting}>
            <LogIn className="h-4 w-4" />
            {submitting ? 'Ingresando...' : 'Iniciar sesión'}
          </Button>
        </form>

        <p className="mt-4 text-center text-xs text-slate-500">
          Paquete: Autenticación y Seguridad — datos en MinIO (app_usuarios)
        </p>
      </Card>
    </div>
  )
}
