import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { KeyRound, Mail, Shield, AlertCircle, CheckCircle2 } from 'lucide-react'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Button, Card, PasswordInput } from '../components/ui'

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
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 via-brand-50/30 to-slate-100 p-6">
      <Card className="w-full max-w-md shadow-xl">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-xl bg-brand-600 p-3 text-white">
            <Shield className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">Recuperar contraseña</h1>
            <p className="text-sm text-slate-500">Te enviaremos un código por correo</p>
          </div>
        </div>

        {step === 1 && (
          <form onSubmit={handleRequestCode} className="space-y-4">
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">Correo registrado</span>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-3 text-sm focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
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
            <p className="text-sm text-slate-600">
              Revisa tu bandeja (y spam). Código enviado a <strong>{email}</strong>
            </p>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">Código de 6 dígitos</span>
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-center text-lg tracking-widest focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
                required
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">Nueva contraseña</span>
              <PasswordInput
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                minLength={8}
                required
                autoComplete="new-password"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">Confirmar contraseña</span>
              <PasswordInput
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                minLength={8}
                required
                autoComplete="new-password"
              />
            </label>
            {error && <ErrorBox message={error} />}
            <Button type="submit" className="w-full justify-center" disabled={submitting}>
              <KeyRound className="h-4 w-4" />
              {submitting ? 'Guardando...' : 'Cambiar contraseña'}
            </Button>
            <button
              type="button"
              className="w-full text-sm text-brand-600 hover:underline"
              onClick={() => setStep(1)}
            >
              Reenviar código
            </button>
          </form>
        )}

        {step === 3 && (
          <div className="space-y-4 text-center">
            <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-600" />
            <p className="text-sm text-slate-700">{message}</p>
            <Link
              to="/login"
              className="inline-flex w-full justify-center rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-700"
            >
              Ir a iniciar sesión
            </Link>
          </div>
        )}

        <p className="mt-6 text-center text-sm text-slate-500">
          <Link to="/login" className="text-brand-600 hover:underline">
            Volver al login
          </Link>
        </p>
      </Card>
    </div>
  )
}

function ErrorBox({ message }) {
  return (
    <div className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800">
      <AlertCircle className="h-5 w-5 shrink-0" />
      <p>{message}</p>
    </div>
  )
}

function SuccessBox({ message }) {
  return (
    <div className="flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
      <CheckCircle2 className="h-5 w-5 shrink-0" />
      <p>{message}</p>
    </div>
  )
}
