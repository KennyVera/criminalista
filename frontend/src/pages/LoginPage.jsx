import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { LogIn, AlertCircle, Lock, ShieldCheck, ArrowLeft, MailCheck } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { Button, Card, PasswordInput, Input, Label } from '../components/ui'
import BrandLogo from '../components/layout/BrandLogo'
import { useAppConfig } from '../context/AppConfigContext'
import {
  SESSION_REVOKED_MESSAGE,
  SESSION_REVOKED_STORAGE_KEY,
} from '../constants/sessionMessages'

export default function LoginPage() {
  const { login, verifyMfa, resendMfa, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [email, setEmail] = useState('kennyvera43@gmail.com')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [sessionNotice, setSessionNotice] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const { appName, subtitle, iconUrl } = useAppConfig()

  // Segundo factor (2FA por correo) para administradores.
  const [stage, setStage] = useState('credentials') // 'credentials' | 'mfa'
  const [mfaEmail, setMfaEmail] = useState('')
  const [mfaCode, setMfaCode] = useState('')
  const [mfaNotice, setMfaNotice] = useState('')
  const [resending, setResending] = useState(false)

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
      const res = await login(email.trim(), password)
      if (res?.mfaRequired) {
        setMfaEmail(res.email || email.trim())
        setMfaNotice(res.message || 'Te enviamos un código de verificación a tu correo.')
        setMfaCode('')
        setStage('mfa')
        return
      }
      navigate('/', { replace: true })
    } catch (err) {
      if (err.code === 'SYSTEM_RECOVERY') {
        navigate('/recuperacion', { replace: true })
        return
      }
      setError(err.message || 'No se pudo iniciar sesión')
    } finally {
      setSubmitting(false)
    }
  }

  const handleVerify = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await verifyMfa(mfaEmail, mfaCode.trim())
      navigate('/', { replace: true })
    } catch (err) {
      if (err.code === 'MFA_EXPIRED') {
        setStage('credentials')
        setPassword('')
        setError(err.message || 'El código expiró. Inicia sesión de nuevo.')
        return
      }
      setError(err.message || 'No se pudo verificar el código')
    } finally {
      setSubmitting(false)
    }
  }

  const handleResend = async () => {
    setError(null)
    setMfaNotice('')
    setResending(true)
    try {
      await resendMfa(mfaEmail)
      setMfaNotice('Te enviamos un código nuevo a tu correo.')
    } catch (err) {
      setError(err.message || 'No se pudo reenviar el código')
    } finally {
      setResending(false)
    }
  }

  const backToCredentials = () => {
    setStage('credentials')
    setError(null)
    setMfaCode('')
    setPassword('')
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#F8FAFC] p-6">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgb(99_102_241/0.08),transparent)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-2/3 w-2/3 bg-[radial-gradient(ellipse_at_bottom_right,rgb(139_92_246/0.06),transparent)]" />

      <div className="relative w-full max-w-[420px] animate-fade-up">
        <div className="mb-8 flex flex-col items-center text-center">
          {iconUrl ? (
            <img
              src={iconUrl}
              alt={appName}
              className="mb-4 h-14 w-14 rounded-[20px] object-cover shadow-lg"
            />
          ) : (
            <BrandLogo className="mb-4 h-14 w-14" />
          )}
          <p className="sidebar-brand-line text-sm">
            CRIMETRACK <span className="sidebar-brand-line--light">ANALYTICS</span>
          </p>
          <p className="mt-1 text-sm text-[#64748B]">
            {subtitle || 'Analítica criminal institucional'}
          </p>
        </div>

        <Card static className="p-8">
          {stage === 'credentials' ? (
            <>
              <div className="mb-8 text-center">
                <div className="page-icon mx-auto mb-5">
                  <Lock className="h-7 w-7" strokeWidth={1.75} />
                </div>
                <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">
                  Iniciar sesión
                </h1>
                <p className="mt-2 text-sm text-[#64748B]">
                  Acceso seguro para investigadores y personal institucional
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                <label className="block">
                  <Label>Correo electrónico</Label>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="username"
                    placeholder="usuario@institucion.gov"
                  />
                </label>
                <label className="block">
                  <Label>Contraseña</Label>
                  <PasswordInput
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    placeholder="••••••••"
                  />
                </label>

                {sessionNotice && (
                  <div className="alert-banner alert-banner--warning">
                    <AlertCircle className="h-5 w-5 shrink-0" />
                    <p>{sessionNotice}</p>
                  </div>
                )}

                {error && (
                  <div className="alert-banner alert-banner--error">
                    <AlertCircle className="h-5 w-5 shrink-0" />
                    <p>{error}</p>
                  </div>
                )}

                <div className="flex justify-end pt-1">
                  <Link
                    to="/recuperar-contrasena"
                    className="text-sm font-medium text-[#6366F1] transition hover:text-[#4F46E5]"
                  >
                    ¿Olvidaste tu contraseña?
                  </Link>
                </div>

                <Button type="submit" className="w-full" size="lg" disabled={submitting}>
                  <LogIn className="h-4 w-4" />
                  {submitting ? 'Ingresando…' : 'Iniciar sesión'}
                </Button>
              </form>
            </>
          ) : (
            <>
              <div className="mb-8 text-center">
                <div className="page-icon mx-auto mb-5">
                  <ShieldCheck className="h-7 w-7" strokeWidth={1.75} />
                </div>
                <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">
                  Verificación en dos pasos
                </h1>
                <p className="mt-2 text-sm text-[#64748B]">
                  Ingresa el código de 6 dígitos enviado a{' '}
                  <span className="font-semibold text-[#0F172A]">{mfaEmail}</span>
                </p>
              </div>

              <form onSubmit={handleVerify} className="space-y-5">
                {mfaNotice && (
                  <div className="alert-banner alert-banner--success">
                    <MailCheck className="h-5 w-5 shrink-0" />
                    <p>{mfaNotice}</p>
                  </div>
                )}

                <label className="block">
                  <Label>Código de verificación</Label>
                  <Input
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    maxLength={6}
                    value={mfaCode}
                    onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ''))}
                    required
                    autoFocus
                    placeholder="••••••"
                    className="text-center text-lg font-semibold tracking-[0.5em]"
                  />
                </label>

                {error && (
                  <div className="alert-banner alert-banner--error">
                    <AlertCircle className="h-5 w-5 shrink-0" />
                    <p>{error}</p>
                  </div>
                )}

                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  disabled={submitting || mfaCode.length < 6}
                >
                  <ShieldCheck className="h-4 w-4" />
                  {submitting ? 'Verificando…' : 'Verificar e ingresar'}
                </Button>

                <div className="flex items-center justify-between pt-1">
                  <button
                    type="button"
                    onClick={backToCredentials}
                    className="inline-flex items-center gap-1.5 text-sm font-medium text-[#64748B] transition hover:text-[#0F172A]"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    Volver
                  </button>
                  <button
                    type="button"
                    onClick={handleResend}
                    disabled={resending}
                    className="text-sm font-medium text-[#6366F1] transition hover:text-[#4F46E5] disabled:opacity-50"
                  >
                    {resending ? 'Reenviando…' : 'Reenviar código'}
                  </button>
                </div>
              </form>
            </>
          )}
        </Card>

        <p className="mt-8 text-center text-xs text-[#94A3B8]">
          © {new Date().getFullYear()} CrimeTrack Analytics · Plataforma institucional
        </p>
      </div>
    </div>
  )
}
