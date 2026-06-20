
import { AlertTriangle } from 'lucide-react'
import { Button } from './ui'

export default function ConfirmDialog({ open, title, message, onConfirm, onCancel, loading }) {
  if (!open) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm"
      role="alertdialog"
      aria-modal="true"
    >
      <div className="w-full max-w-md overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-2xl shadow-slate-900/10">
        <div className="border-b border-red-100 bg-gradient-to-r from-red-50 to-white px-6 py-5">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-100 text-red-600">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{message}</p>
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-2 px-6 py-4">
          <Button variant="secondary" onClick={onCancel}>
            Cancelar
          </Button>
          <Button variant="danger" onClick={onConfirm} disabled={loading}>
            {loading ? 'Eliminando…' : 'Eliminar'}
          </Button>
        </div>
      </div>
    </div>
  )
}
