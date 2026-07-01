import { useEffect, useRef, useState } from 'react'
import {
  Database,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
} from 'lucide-react'
import { api } from '../api/client'
import { Button, Card, Badge, Input } from '../components/ui'

const POLL_MS = 1500
const MIN_BATCH = 1
const MAX_BATCH = 300_000
const DEFAULT_BATCH = 50_000

const PHASE = {
  form: 'form',
  syncing: 'syncing',
  done: 'done',
  error: 'error',
}

function ProgressBar({ percent, label }) {
  return (
    <div>
      {label && (
        <div className="mb-2 flex justify-between text-sm">
          <span className="font-medium text-slate-700">{label}</span>
          <span className="font-mono text-xs font-semibold text-brand-600">{percent}%</span>
        </div>
      )}
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100 ring-1 ring-slate-200/80">
        <div
          className="h-full rounded-full bg-gradient-to-r from-brand-500 via-brand-600 to-indigo-600 transition-all duration-300 shadow-sm"
          style={{ width: `${Math.min(100, percent)}%` }}
        />
      </div>
    </div>
  )
}

export default function GenerateDataPage() {
  const [phase, setPhase] = useState(PHASE.form)
  const [stats, setStats] = useState(null)
  const [statsLoading, setStatsLoading] = useState(true)
  const [syncResult, setSyncResult] = useState(null)
  const [errorMsg, setErrorMsg] = useState(null)
  const [statusHint, setStatusHint] = useState(null)
  const [syncProgress, setSyncProgress] = useState({ percent: 0, message: '' })
  const [batchSize, setBatchSize] = useState(String(DEFAULT_BATCH))
  const [batchTouched, setBatchTouched] = useState(false)
  const cancelRef = useRef(false)

  useEffect(() => {
    let cancelled = false
    setStatsLoading(true)
    api
      .syncPocketBaseStats()
      .then((data) => {
        if (!cancelled) setStats(data)
      })
      .catch(() => {
        if (!cancelled) setStats(null)
      })
      .finally(() => {
        if (!cancelled) setStatsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [phase])

  useEffect(() => {
    if (!stats || batchTouched) return
    const pending = Math.max(
      0,
      Number(stats.pending_estimate ?? stats.pocketbase_crimes_220k - stats.minio_fact_crimes)
    )
    const suggested = Math.min(MAX_BATCH, Math.max(MIN_BATCH, pending || DEFAULT_BATCH))
    setBatchSize(String(suggested))
  }, [stats, batchTouched])

  const reset = () => {
    setPhase(PHASE.form)
    setSyncResult(null)
    setErrorMsg(null)
    setStatusHint(null)
    setSyncProgress({ percent: 0, message: '' })
    cancelRef.current = false
  }

  const pollSyncStatus = (taskId) =>
    api.etlTaskStatus(taskId).catch(() => api.jobStatus(taskId))

  const pollTask = (fetchStatus, onUpdate, onDone) =>
    new Promise((resolve, reject) => {
      const tick = async () => {
        if (cancelRef.current) {
          resolve(null)
          return
        }
        try {
          const st = await fetchStatus()
          onUpdate(st)
          if (st.status === 'completed') {
            onDone(st)
            resolve(st)
            return
          }
          if (st.status === 'failed') {
            reject(new Error(st.error || st.result?.error || 'Tarea fallida'))
            return
          }
        } catch (err) {
          reject(err)
          return
        }
        setTimeout(tick, POLL_MS)
      }
      tick()
    })

  const parsedBatch = Number(batchSize)
  const batchInvalid =
    batchSize === '' ||
    !Number.isFinite(parsedBatch) ||
    !Number.isInteger(parsedBatch) ||
    parsedBatch < MIN_BATCH ||
    parsedBatch > MAX_BATCH
  const batchErrorMsg = batchInvalid
    ? `Ingrese un entero entre ${MIN_BATCH.toLocaleString('es-CO')} y ${MAX_BATCH.toLocaleString('es-CO')}.`
    : null

  const handleSync = async () => {
    if (batchInvalid) return
    cancelRef.current = false
    setPhase(PHASE.syncing)
    setErrorMsg(null)
    setSyncResult(null)
    setSyncProgress({ percent: 0, message: 'Encolando sincronización...' })
    setStatusHint('Extracción por lotes desde PocketBase (solo registros nuevos si aplica).')

    try {
      const payload = {
        mode: 'auto',
        export_raw_copy: true,
        cantidad_registros: parsedBatch,
      }
      const queued = await api.syncPocketBase(payload)
      await pollTask(
        () => pollSyncStatus(queued.task_id),
        (st) => {
          setSyncProgress({
            percent: st.percent ?? (st.status === 'completed' ? 100 : 0),
            message: st.message || st.phase || 'Procesando...',
          })
          if (st.new_count != null) {
            setStatusHint(`${st.new_count.toLocaleString('es-CO')} registros nuevos detectados`)
          }
        },
        (st) => {
          setSyncResult(st.result || st)
          setSyncProgress({ percent: 100, message: 'Completado' })
          setPhase(PHASE.done)
        }
      )
      if (cancelRef.current) reset()
    } catch (err) {
      setErrorMsg(err.message)
      setPhase(PHASE.error)
    }
  }

  const recommendedMode = stats?.recommended_mode || 'auto'
  const modeLabel =
    recommendedMode === 'incremental'
      ? 'incremental (solo nuevos)'
      : 'completo (primera carga o reconstrucción)'

  return (
    <section className="mx-auto max-w-4xl space-y-6">
      <header className="border-b border-slate-200/80 pb-6">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-indigo-600 text-white shadow-lg shadow-brand-600/25">
            <RefreshCw className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              Sincronizar datos desde PocketBase
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Extrae <strong className="text-slate-700">crimes_220k</strong> por lotes y carga el
              modelo analítico en <strong className="text-slate-700">MinIO</strong> (Parquet
              consolidado + tablas resumen para el dashboard).
            </p>
          </div>
        </div>
      </header>

      {(phase === PHASE.form || phase === PHASE.error) && (
        <Card className="border-brand-200/40 bg-gradient-to-br from-brand-50/20 to-white">
          <div className="space-y-4">
            <div className="rounded-xl border border-slate-200/80 bg-white/80 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Estado del dataset
              </p>
              {statsLoading ? (
                <p className="mt-2 flex items-center gap-2 text-sm text-slate-600">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Consultando PocketBase y MinIO...
                </p>
              ) : stats ? (
                <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
                  <div>
                    <dt className="text-slate-500">PocketBase crimes_220k</dt>
                    <dd className="font-semibold text-slate-900">
                      {Number(stats.pocketbase_crimes_220k).toLocaleString('es-CO')} registros
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">MinIO fact_crimes</dt>
                    <dd className="font-semibold text-slate-900">
                      {Number(stats.minio_fact_crimes).toLocaleString('es-CO')} hechos
                    </dd>
                  </div>
                </dl>
              ) : (
                <p className="mt-2 text-sm text-amber-700">
                  No se pudo leer el estado. Verifica que PocketBase esté en ejecución.
                </p>
              )}
              {!statsLoading && stats && (
                <p className="mt-3 text-xs text-slate-500">
                  Modo recomendado: <strong>{modeLabel}</strong>
                  {stats.pending_estimate > 0 && (
                    <>
                      {' '}
                      · Pendientes estimados:{' '}
                      <strong>{Number(stats.pending_estimate).toLocaleString('es-CO')}</strong>
                    </>
                  )}
                </p>
              )}
            </div>

            {phase === PHASE.error && errorMsg && (
              <div className="flex items-start gap-3 rounded-xl border border-red-200/80 bg-red-50/90 p-3 text-sm text-red-800">
                <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
                <p>{errorMsg}</p>
              </div>
            )}

            <div className="space-y-2">
              <label htmlFor="batch-size" className="block text-sm font-semibold text-slate-800">
                Cantidad de registros a procesar
              </label>
              <Input
                id="batch-size"
                type="number"
                min={MIN_BATCH}
                max={MAX_BATCH}
                step={1}
                inputMode="numeric"
                value={batchSize}
                onChange={(e) => {
                  setBatchTouched(true)
                  setBatchSize(e.target.value)
                }}
                aria-invalid={batchInvalid}
                aria-describedby={batchErrorMsg ? 'batch-size-error' : undefined}
                className={batchInvalid ? 'border-red-300 ring-red-200' : ''}
              />
              {batchErrorMsg ? (
                <p id="batch-size-error" className="text-sm text-red-600">
                  {batchErrorMsg}
                </p>
              ) : (
                <p className="text-xs text-slate-500">
                  Máximo por ejecución: {MAX_BATCH.toLocaleString('es-CO')} registros nuevos
                  (sin duplicados).
                </p>
              )}
            </div>

            <div className="flex flex-wrap gap-3">
              <Button type="button" onClick={handleSync} disabled={batchInvalid}>
                <RefreshCw className="h-4 w-4" />
                Sincronizar / Extraer datos
              </Button>
            </div>
            <p className="text-xs leading-relaxed text-slate-500">
              La sincronización corre en segundo plano (Celery o hilo daemon) sin bloquear el
              navegador. Extrae por paginación desde PocketBase, transforma al modelo estrella y
              actualiza MinIO + resumen del dashboard.
            </p>
          </div>
        </Card>
      )}

      {phase === PHASE.syncing && (
        <Card>
          <div className="mb-4 flex items-center gap-3 rounded-xl bg-brand-50/50 px-4 py-3">
            <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
            <p className="font-medium text-slate-800">Extrayendo y cargando datos...</p>
          </div>
          <ProgressBar percent={syncProgress.percent} label={syncProgress.message || 'Progreso ETL'} />
          {statusHint && <p className="mt-3 text-sm text-slate-500">{statusHint}</p>}
          <Button
            variant="secondary"
            className="mt-4"
            type="button"
            onClick={() => {
              cancelRef.current = true
            }}
          >
            Cancelar seguimiento
          </Button>
        </Card>
      )}

      {phase === PHASE.done && syncResult && (
        <Card className="overflow-hidden border-emerald-200/80 bg-gradient-to-br from-emerald-50/60 to-white">
          <div className="flex items-start gap-4 p-5">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-emerald-100">
              <CheckCircle2 className="h-7 w-7 text-emerald-600" />
            </div>
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-semibold text-emerald-900">Sincronización completada</p>
                {syncResult.sync_mode && (
                  <Badge tone="green">{syncResult.sync_mode}</Badge>
                )}
              </div>
              <p className="mt-1 text-sm text-emerald-800">{syncResult.message}</p>
              {syncResult.new_records != null && (
                <p className="mt-2 text-sm text-slate-700">
                  Registros nuevos procesados:{' '}
                  <strong>{Number(syncResult.new_records).toLocaleString('es-CO')}</strong>
                  {syncResult.cantidad_registros != null && (
                    <span className="text-slate-500">
                      {' '}
                      (límite: {Number(syncResult.cantidad_registros).toLocaleString('es-CO')})
                    </span>
                  )}
                </p>
              )}
              {syncResult.skipped_duplicates != null && syncResult.skipped_duplicates > 0 && (
                <p className="text-sm text-slate-600">
                  Duplicados omitidos:{' '}
                  <strong>{Number(syncResult.skipped_duplicates).toLocaleString('es-CO')}</strong>
                </p>
              )}
              {syncResult.fact_before != null && syncResult.fact_after != null && (
                <p className="text-sm text-slate-700">
                  Hechos: {Number(syncResult.fact_before).toLocaleString('es-CO')} →{' '}
                  {Number(syncResult.fact_after).toLocaleString('es-CO')}
                </p>
              )}
              {syncResult.collections && (
                <ul className="mt-3 grid gap-1 text-sm text-slate-700 sm:grid-cols-2">
                  {Object.entries(syncResult.collections).map(([name, n]) => (
                    <li key={name}>
                      <span className="font-medium">{name}:</span>{' '}
                      {Number(n).toLocaleString('es-CO')} filas
                    </li>
                  ))}
                </ul>
              )}
              {syncResult.dimensions && (
                <ul className="mt-3 grid gap-1 text-sm text-slate-700 sm:grid-cols-2">
                  {Object.entries(syncResult.dimensions).map(([name, meta]) => (
                    <li key={name}>
                      <span className="font-medium">{name}:</span> +{meta.new} (total {meta.total})
                    </li>
                  ))}
                </ul>
              )}
              <div className="mt-4 flex flex-wrap gap-2">
                <Button variant="secondary" type="button" onClick={reset}>
                  <Database className="h-4 w-4" />
                  Nueva sincronización
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}
    </section>
  )
}
