import { Loader2, XCircle } from 'lucide-react'
import { Button, Card } from './ui'

const PHASE_LABELS = {
  init: 'Preparando',
  snapshot: 'Resguardando estado actual',
  restore: 'Restaurando tablas',
  restore_done: 'Restauración lista',
  extract: 'Extrayendo PocketBase',
  transform: 'Transformando modelo estrella',
  upload: 'Subiendo a MinIO',
  etl: 'ETL en curso',
  cancelling: 'Cancelando',
  cancelled: 'Cancelado',
  done: 'Completado',
  error: 'Error',
}

export default function RestoreProgressCard({ progress, running, onCancel, canCancel }) {
  if (!running && progress.percent === 0) return null

  const phaseLabel = PHASE_LABELS[progress.phase] || progress.phase || 'Proceso'
  const isCancelling = progress.phase === 'cancelling' || progress.phase === 'cancelled'

  return (
    <Card className="border-brand-200 bg-brand-50/30 p-6">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
          <div>
            <p className="font-semibold text-slate-900">Restauración + ETL automático</p>
            <p className="text-xs text-slate-500">{phaseLabel}</p>
          </div>
        </div>
        {canCancel && onCancel && !isCancelling && (
          <Button
            type="button"
            variant="secondary"
            className="shrink-0 border border-red-200 text-red-700 hover:bg-red-50"
            onClick={onCancel}
          >
            <XCircle className="h-4 w-4" />
            Cancelar
          </Button>
        )}
      </div>
      <div className="mb-2 flex justify-between text-sm">
        <span className="text-slate-600">{progress.message || 'Espere...'}</span>
        <span className="font-mono font-medium text-brand-700">{progress.percent}%</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-gradient-to-r from-brand-500 to-indigo-600 transition-all duration-500"
          style={{ width: `${Math.min(100, progress.percent)}%` }}
        />
      </div>
      <p className="mt-3 text-xs text-slate-500">
        {isCancelling
          ? 'Revirtiendo tablas y modelo analítico al estado previo a esta restauración.'
          : 'Al cancelar, los datos vuelven a como estaban antes de pulsar restaurar. El proceso puede tardar 15–30 min si no se cancela.'}
      </p>
    </Card>
  )
}
