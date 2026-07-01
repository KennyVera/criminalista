import { useState } from 'react'
import { KeyRound, X } from 'lucide-react'
import { api } from '../api/client'
import { Button, PasswordInput } from './ui'
import { useToast } from '../context/ToastContext'

export default function ChangePasswordModal({ open, onClose }) {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const toast = useToast()

  if (!open) return null

  const reset = () => {
    setCurrentPassword('')
    setNewPassword('')
    setConfirmPassword('')
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (newPassword !== confirmPassword) {
      toast.error('Error', 'La confirmación no coincide con la nueva contraseña')
      return
    }
    setLoading(true)
    try {
      await api.authChangePassword(currentPassword, newPassword)
      toast.success('Éxito', 'Contraseña actualizada correctamente')
      handleClose()
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="change-password-title"
    >
      <div className="w-full max-w-md overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-2xl shadow-slate-900/10">
        <div className="flex items-start justify-between border-b border-slate-100 px-6 py-5">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
              <KeyRound className="h-5 w-5" />
            </div>
            <div>
              <h3 id="change-password-title" className="text-lg font-semibold text-slate-900">
                Cambiar contraseña
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                Ingresa tu contraseña actual y la nueva contraseña.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="rounded-xl p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
            aria-label="Cerrar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4 px-6 py-5">
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-slate-600">
              Contraseña actual
            </label>
            <PasswordInput
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-slate-600">
              Nueva contraseña
            </label>
            <PasswordInput
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              autoComplete="new-password"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-slate-600">
              Confirmar nueva contraseña
            </label>
            <PasswordInput
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              autoComplete="new-password"
            />
          </div>
          <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
            <Button type="button" variant="secondary" onClick={handleClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Guardando…' : 'Guardar'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
