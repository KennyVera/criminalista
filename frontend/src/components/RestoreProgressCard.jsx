import { CheckCircle2, Loader2, XCircle } from 'lucide-react'
import { Button, Card } from './ui'

const PHASE_LABELS = {
  init: 'Preparando',
  snapshot: 'Resguardando estado actual',
  restore: 'Restaurando tablas',
  restore_done: 'Restauración lista',
  restore_analytics: 'Restaurando capa analítica',
  summary: 'Finalizando',
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
  const isDone =
    !running &&
    (progress.phase === 'done' ||
      progress.percent >= 100 ||
      /completad/i.test(progress.message || ''))
  const isError = progress.phase === 'error'

  return (
    <Card
      className={`p-6 ${
        isDone
          ? 'border-green-200 bg-green-50/40'
          : isError
            ? 'border-red-200 bg-red-50/30'
            : 'border-brand-200 bg-brand-50/30'
      }`}
    >
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          {isDone ? (
            <CheckCircle2 className="h-5 w-5 text-green-600" />
          ) : (
            <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
          )}
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
        {isDone
          ? 'Proceso finalizado. Puede cerrar esta sección e iniciar sesión con normalidad.'
          : isCancelling
            ? 'Revirtiendo tablas y modelo analítico al estado previo a esta restauración.'
            : running
              ? 'El proceso puede tardar 15–30 min. No cierre esta pestaña hasta ver 100%.'
              : ''}
      </p>
    </Card>
  )
}
