import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { KeyRound, Mail, Shield, AlertCircle, CheckCircle2 } from 'lucide-react'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Button, Card, PasswordInput } from '../components/ui'

const INPUT =
  'w-full rounded-xl border border-slate-200 bg-slate-50/50 py-2.5 text-sm text-slate-900 transition focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-100'

const STEPS = [
  { n: 1, label: 'Correo' },
  { n: 2, label: 'Código' },
  { n: 3, label: 'Listo' },
]

export default function RecoverPasswordPage() {
  const { isAuthenticated } = useAuth()
  const [step, setStep] = useState(1)
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(null)
  const [message, setMessage] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const handleRequestCode = async (e) => {
    e.preventDefault()
    setError(null)
    setMessage(null)
    setSubmitting(true)
    try {
      const res = await api.authRequestPasswordReset(email.trim())
      setMessage(res.message)
      setStep(2)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleReset = async (e) => {
    e.preventDefault()
    setError(null)
    if (newPassword !== confirm) {
      setError('Las contraseñas no coinciden')
      return
    }
    setSubmitting(true)
    try {
      const res = await api.authResetPassword(email.trim(), code.trim(), newPassword)
      setMessage(res.message)
      setStep(3)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 via-brand-50/40 to-slate-100 p-6">
      <Card className="w-full max-w-md overflow-hidden border-slate-200/80 p-0 shadow-2xl shadow-slate-900/10">
        <div className="border-b border-slate-100 bg-gradient-to-r from-brand-50/80 to-white px-6 py-6">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-indigo-600 text-white shadow-lg">
              <Shield className="h-7 w-7" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900">
                Recuperar contraseña
              </h1>
              <p className="text-sm text-slate-500">Te enviaremos un código por correo</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {STEPS.map((s, i) => (
              <div key={s.n} className="flex flex-1 items-center gap-2">
                <div
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold transition ${
                    step >= s.n
                      ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30'
                      : 'bg-slate-200 text-slate-500'
                  }`}
                >
                  {step > s.n ? <CheckCircle2 className="h-4 w-4" /> : s.n}
                </div>
                <span
                  className={`hidden text-xs font-medium sm:inline ${
                    step >= s.n ? 'text-brand-700' : 'text-slate-400'
                  }`}
                >
                  {s.label}
                </span>
                {i < STEPS.length - 1 && (
                  <div
                    className={`h-0.5 flex-1 rounded ${step > s.n ? 'bg-brand-400' : 'bg-slate-200'}`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="p-6">
          {step === 1 && (
            <form onSubmit={handleRequestCode} className="space-y-4">
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Correo registrado
                </span>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={`${INPUT} pl-10 pr-3`}
                    required
                  />
                </div>
              </label>
              {error && <ErrorBox message={error} />}
              {message && <SuccessBox message={message} />}
              <Button type="submit" className="w-full justify-center" disabled={submitting}>
                {submitting ? 'Enviando...' : 'Enviar código'}
              </Button>
            </form>
          )}

          {step === 2 && (
            <form onSubmit={handleReset} className="space-y-4">
              <p className="rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2.5 text-sm text-slate-600">
                Revisa tu bandeja (y spam). Código enviado a{' '}
                <strong className="text-slate-800">{email}</strong>
              </p>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Código de 6 dígitos
                </span>
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                  className={`${INPUT} px-3 text-center text-lg tracking-[0.4em]`}
                  required
                />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Nueva contraseña
                </span>
                <PasswordInput
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  minLength={8}
                  required
                  autoComplete="new-password"
                  inputClassName="bg-slate-50/50"
                />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Confirmar contraseña
                </span>
                <PasswordInput
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  minLength={8}
                  required
                  autoComplete="new-password"
                  inputClassName="bg-slate-50/50"
                />
              </label>
              {error && <ErrorBox message={error} />}
              <Button type="submit" className="w-full justify-center" disabled={submitting}>
                <KeyRound className="h-4 w-4" />
                {submitting ? 'Guardando...' : 'Cambiar contraseña'}
              </Button>
              <button
                type="button"
                className="w-full text-sm font-medium text-brand-600 transition hover:text-brand-700"
                onClick={() => setStep(1)}
              >
                Reenviar código
              </button>
            </form>
          )}

          {step === 3 && (
            <div className="space-y-4 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-50">
                <CheckCircle2 className="h-10 w-10 text-emerald-600" />
              </div>
              <p className="text-sm text-slate-700">{message}</p>
              <Link to="/login" className="block">
                <Button className="w-full justify-center">Ir a iniciar sesión</Button>
              </Link>
            </div>
          )}

          <p className="mt-6 text-center text-sm text-slate-500">
            <Link to="/login" className="font-medium text-brand-600 transition hover:text-brand-700">
              Volver al login
            </Link>
          </p>
        </div>
      </Card>
    </div>
  )
}

function ErrorBox({ message }) {
  return (
    <div className="flex items-start gap-2.5 rounded-xl border border-red-200/80 bg-red-50/90 p-3 text-sm text-red-800">
      <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
      <p>{message}</p>
    </div>
  )
}

function SuccessBox({ message }) {
  return (
    <div className="flex items-start gap-2.5 rounded-xl border border-emerald-200/80 bg-emerald-50/90 p-3 text-sm text-emerald-800">
      <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-500" />
      <p>{message}</p>
    </div>
  )
}
