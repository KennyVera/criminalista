import { useRef, useState } from 'react'
import {
  Sparkles,
  Database,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Layers,
} from 'lucide-react'
import { api } from '../api/client'
import { Button, Card, Badge } from '../components/ui'

const MAX_TOTAL = 500_000
const POLL_MS = 1500
const PREVIEW_MAX = 8
/** Requisito académico: +100k históricos hacia ~300k */
const REALISTIC_100K = 100_000

const PHASE = {
  form: 'form',
  generating: 'generating',
  preview: 'preview',
  etl: 'etl',
  etlDone: 'etlDone',
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
  const [count, setCount] = useState(50)
  const [phase, setPhase] = useState(PHASE.form)
  const [progress, setProgress] = useState({
    done: 0,
    total: 0,
    created: 0,
    errors: 0,
    percent: 0,
  })
  const [previewRows, setPreviewRows] = useState([])
  const [genSummary, setGenSummary] = useState(null)
  const [etlResult, setEtlResult] = useState(null)
  const [errorMsg, setErrorMsg] = useState(null)
  const [statusHint, setStatusHint] = useState(null)
  const [etlProgress, setEtlProgress] = useState({ percent: 0, message: '' })
  const cancelRef = useRef(false)

  const reset = () => {
    setPhase(PHASE.form)
    setProgress({ done: 0, total: 0, created: 0, errors: 0, percent: 0 })
    setPreviewRows([])
    setGenSummary(null)
    setEtlResult(null)
    setErrorMsg(null)
    setStatusHint(null)
    setEtlProgress({ percent: 0, message: '' })
    cancelRef.current = false
  }

  const finishGeneration = (result, total) => {
    const samples = result.samples || []
    setPreviewRows(samples.slice(-PREVIEW_MAX))
    setGenSummary({
      created: result.raw?.created ?? result.inserted_facts ?? 0,
      errors: result.raw?.errors ?? 0,
      total,
    })
    setPhase(PHASE.preview)
  }

  const pollGenerateStatus = (taskId) =>
    api.generateFakeDataStatus(taskId).catch(() => api.jobStatus(taskId))

  const pollEtlStatus = (taskId) =>
    api.etlTaskStatus(taskId).catch(() => api.etlStatus(taskId))

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

  const handleRealistic100k = async () => {
    const total = REALISTIC_100K
    cancelRef.current = false
    setPhase(PHASE.generating)
    setErrorMsg(null)
    setStatusHint('Distribuyendo 100.000 hechos entre 2001 y 2026...')
    setPreviewRows([])
    setGenSummary(null)
    setEtlResult(null)
    setProgress({ done: 0, total, created: 0, errors: 0, percent: 0 })

    try {
      setStatusHint('Tarea en segundo plano (lotes de 5.000)...')
      const queued = await api.generateFakeDataAsync(total, true)
      await pollTask(
        () => pollGenerateStatus(queued.task_id),
        (st) => {
          setProgress({
            done: st.done ?? 0,
            total: st.total ?? total,
            created: st.created ?? 0,
            errors: st.errors ?? 0,
            percent: st.percent ?? 0,
          })
          if (st.last_sample) {
            setPreviewRows((prev) => [...prev, st.last_sample].slice(-PREVIEW_MAX))
          }
        },
        (st) => {
          finishGeneration(st.result || st, total)
        }
      )
    } catch (err) {
      setErrorMsg(err.message)
      setPhase(PHASE.error)
    }
  }

  const handleGenerate = async () => {
    const total = Math.min(MAX_TOTAL, Math.max(1, Number(count) || 0))
    cancelRef.current = false
    setPhase(PHASE.generating)
    setErrorMsg(null)
    setStatusHint(null)
    setPreviewRows([])
    setGenSummary(null)
    setEtlResult(null)
    setProgress({ done: 0, total, created: 0, errors: 0, percent: 0 })

    try {
      setStatusHint('Tarea en segundo plano (lotes de 5.000, sin bloquear el navegador)...')
      const queued = await api.generateFakeDataAsync(total)
      await pollTask(
        () => pollGenerateStatus(queued.task_id),
        (st) => {
          setStatusHint(
            st.status === 'pending' || st.status === 'queued'
              ? 'En cola / iniciando...'
              : null
          )
          setProgress({
            done: st.done ?? 0,
            total: st.total ?? total,
            created: st.created ?? 0,
            errors: st.errors ?? 0,
            percent: st.percent ?? 0,
          })
          if (st.last_sample) {
            setPreviewRows((prev) => {
              const next = [...prev, st.last_sample]
              return next.slice(-PREVIEW_MAX)
            })
          }
        },
        (st) => {
          const result = st.result || st
          finishGeneration(result, total)
        }
      )
      if (cancelRef.current) reset()
    } catch (err) {
      setErrorMsg(err.message)
      setPhase(PHASE.error)
    }
  }

  const handleFeedDimensions = async () => {
    setPhase(PHASE.etl)
    setErrorMsg(null)
    setEtlProgress({ percent: 0, message: 'Encolando ETL...' })
    try {
      const queued = await api.runEtlToMinioAsync()
      await pollTask(
        () => pollEtlStatus(queued.task_id),
        (st) => {
          setEtlProgress({
            percent: st.percent ?? (st.status === 'completed' ? 100 : 0),
            message: st.message || st.phase || 'Procesando...',
          })
        },
        (st) => {
          setEtlResult(st.result || st)
          setEtlProgress({ percent: 100, message: 'Completado' })
          setPhase(PHASE.etlDone)
        }
      )
    } catch (err) {
      setErrorMsg(err.message)
      setPhase(PHASE.preview)
    }
  }

  return (
    <section className="mx-auto max-w-4xl space-y-6">
      <header className="border-b border-slate-200/80 pb-6">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-indigo-600 text-white shadow-lg shadow-brand-600/25">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              Generar datos ficticios
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Faker inserta registros en <strong className="text-slate-700">crimes_220k</strong>{' '}
              (PocketBase). Opcionalmente actualiza dimensiones y hechos en MinIO.
            </p>
          </div>
        </div>
      </header>

      {(phase === PHASE.form || phase === PHASE.error) && (
        <Card className="border-brand-200/40 bg-gradient-to-br from-brand-50/20 to-white">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleGenerate()
            }}
            className="space-y-4"
          >
            <label className="block max-w-xs">
              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Cantidad de registros
              </span>
              <input
                type="number"
                min={1}
                max={MAX_TOTAL}
                value={count}
                onChange={(e) => setCount(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2.5 text-sm text-slate-900 transition focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-100"
              />
              <span className="mt-1.5 block text-xs leading-relaxed text-slate-500">
                La generación corre en segundo plano (lotes de 5.000, inserción paralela). Hasta{' '}
                {MAX_TOTAL.toLocaleString('es-CO')} registros sin bloquear el navegador.
              </span>
            </label>

            {phase === PHASE.error && errorMsg && (
              <div className="flex items-start gap-3 rounded-xl border border-red-200/80 bg-red-50/90 p-3 text-sm text-red-800">
                <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
                <p>{errorMsg}</p>
              </div>
            )}

            <div className="flex flex-wrap gap-3">
              <Button type="submit">
                <Sparkles className="h-4 w-4" />
                Generar registros
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={(e) => {
                  e.preventDefault()
                  handleRealistic100k()
                }}
              >
                <Layers className="h-4 w-4" />
                +100k históricos (~300k)
              </Button>
            </div>
            <p className="text-xs text-slate-500">
              El botón histórico reparte fechas entre 2001 y 2026 para que las tendencias
              delictivas del dashboard se vean continuas. Después ejecuta ETL a MinIO.
            </p>
          </form>
        </Card>
      )}

      {phase === PHASE.generating && (
        <Card>
          <div className="mb-4 flex items-center gap-3 rounded-xl bg-brand-50/50 px-4 py-3">
            <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
            <p className="font-medium text-slate-800">Generando datos con Faker...</p>
          </div>
          <ProgressBar
            percent={progress.percent}
            label={`${progress.done} / ${progress.total} registros`}
          />
          <p className="mt-3 text-sm text-emerald-600">Creados: {progress.created}</p>
          {statusHint && (
            <p className="mt-2 text-sm text-slate-500">{statusHint}</p>
          )}
          <Button
            variant="secondary"
            className="mt-4"
            type="button"
            onClick={() => {
              cancelRef.current = true
            }}
          >
            Cancelar
          </Button>
        </Card>
      )}

      {(phase === PHASE.preview || phase === PHASE.etl || phase === PHASE.etlDone) && (
        <>
          <Card className="overflow-hidden p-0">
            <div className="border-b border-emerald-100 bg-emerald-50/50 px-5 py-4">
              <div className="flex flex-wrap items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                <p className="font-semibold text-slate-900">
                  {genSummary?.created} registros insertados en crimes_220k
                </p>
                <Badge tone="green">PocketBase</Badge>
              </div>
            </div>

            <div className="p-5">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Vista previa (ultimos {previewRows.length} generados)
            </h3>
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead className="border-b border-slate-200 bg-slate-50/80">
                  <tr>
                    <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Caso</th>
                    <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Tipo</th>
                    <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Bloque</th>
                    <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Distrito</th>
                    <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Fecha</th>
                    <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Arresto</th>
                  </tr>
                </thead>
                <tbody>
                  {previewRows.map((row) => (
                    <tr key={row.id || row.pb_id} className="border-b border-slate-100 transition hover:bg-slate-50/60">
                      <td className="px-4 py-3 font-medium text-slate-900">{row.case_number}</td>
                      <td className="px-4 py-3 text-slate-700">{row.primary_type}</td>
                      <td className="max-w-[160px] truncate px-4 py-3 text-slate-600">{row.block}</td>
                      <td className="px-4 py-3 text-slate-700">{row.district}</td>
                      <td className="max-w-[140px] truncate px-4 py-3 text-xs text-slate-500">{row.date}</td>
                      <td className="px-4 py-3 text-slate-700">{row.arrest}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            </div>
          </Card>

          {errorMsg && phase === PHASE.preview && (
            <div className="flex items-start gap-3 rounded-xl border border-red-200/80 bg-red-50/90 p-3 text-sm text-red-800">
              <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
              <p>{errorMsg}</p>
            </div>
          )}

          {phase === PHASE.preview && (
            <Card className="overflow-hidden border-brand-200/60 bg-gradient-to-br from-brand-50/40 to-white">
              <div className="flex items-start gap-4 p-5">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-100 text-brand-600">
                  <Layers className="h-6 w-6" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-slate-900">
                    Deseas alimentar tus tablas de Dimensiones?
                  </p>
                  <p className="mt-1 text-sm text-slate-600">
                    Si eliges Si, se ejecuta el ETL hacia MinIO (dimensiones + fact_crimes).
                  </p>
                  <div className="mt-4 flex flex-wrap gap-3">
                    <Button type="button" onClick={handleFeedDimensions}>
                      <Database className="h-4 w-4" />
                      Si, actualizar MinIO
                    </Button>
                    <Button variant="secondary" type="button" onClick={reset}>
                      No, solo raw en PocketBase
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {phase === PHASE.etl && (
            <Card>
              <div className="mb-4 flex items-center gap-3 rounded-xl bg-brand-50/50 px-4 py-3">
                <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
                <div>
                  <p className="font-medium text-slate-900">Alimentando dimensiones en MinIO...</p>
                  <p className="text-sm text-slate-500">
                    {etlProgress.message ||
                      'Extraccion paralela, transformacion vectorizada y subida Parquet.'}
                  </p>
                </div>
              </div>
              <ProgressBar
                percent={etlProgress.percent}
                label="Progreso ETL"
              />
            </Card>
          )}

          {phase === PHASE.etlDone && etlResult && (
            <Card className="overflow-hidden border-emerald-200/80 bg-gradient-to-br from-emerald-50/60 to-white">
              <div className="flex items-start gap-4 p-5">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-emerald-100">
                  <CheckCircle2 className="h-7 w-7 text-emerald-600" />
                </div>
                <div>
                  <p className="font-semibold text-emerald-900">MinIO actualizado</p>
                  <p className="mt-1 text-sm text-emerald-800">{etlResult.message}</p>
                  {etlResult.collections && (
                    <ul className="mt-3 grid gap-1 text-sm text-slate-700 sm:grid-cols-2">
                      {Object.entries(etlResult.collections).map(([name, n]) => (
                        <li key={name}>
                          <span className="font-medium">{name}:</span>{' '}
                          {Number(n).toLocaleString('es-CO')} filas
                        </li>
                      ))}
                    </ul>
                  )}
                  <Button variant="secondary" className="mt-4" type="button" onClick={reset}>
                    Generar mas registros
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </>
      )}
    </section>
  )
}
