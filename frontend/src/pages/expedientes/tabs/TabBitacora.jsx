import { useCallback, useEffect, useState } from 'react'
import { Clock, PenLine, CheckCircle2, XCircle, Lock } from 'lucide-react'
import { expedientesApi } from '../../../api/expedientes'
import { Button, Card, Spinner } from '../../../components/ui'
import { useToast } from '../../../context/ToastContext'

const ESTADOS = ['Abierto', 'En investigación', 'Resuelto', 'Cerrado', 'Archivado']
const ESTADOS_CIERRE = ['Cerrado', 'Archivado']

const CHECK_LABELS = {
  involucrados: 'Al menos un involucrado registrado',
  evidencias: 'Al menos una evidencia cargada',
  custodia: 'Cadena de custodia íntegra (sin evidencias destruidas)',
  avance: 'Avance del caso al 100%',
}

export default function TabBitacora({ caseNumber, avanceInicial = 0, estadoInicial = 'En investigación' }) {
  const toast = useToast()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [nota, setNota] = useState('')
  const [avance, setAvance] = useState(avanceInicial)
  const [estado, setEstado] = useState(estadoInicial)
  const [req, setReq] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await expedientesApi.bitacora(caseNumber)
      setItems(res.items || [])
      if (res.items?.[0]) {
        setAvance(Number(res.items[0].avance_pct) || avance)
        setEstado(res.items[0].estado_caso || estado)
      }
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setLoading(false)
    }
  }, [caseNumber, toast])

  const loadReq = useCallback(async () => {
    try {
      setReq(await expedientesApi.cierreRequisitos(caseNumber))
    } catch {
      setReq(null)
    }
  }, [caseNumber])

  useEffect(() => {
    load()
    loadReq()
  }, [load, loadReq])

  const isClosing = ESTADOS_CIERRE.includes(estado)

  const submit = async (e) => {
    e.preventDefault()
    if (!nota.trim()) {
      toast.error('Nota requerida', 'Escriba el avance de la investigación')
      return
    }
    try {
      await expedientesApi.addBitacora(caseNumber, {
        nota,
        avance_pct: avance,
        estado_caso: estado,
      })
      toast.success('Registrado', 'Entrada agregada a la bitácora')
      setNota('')
      load()
      loadReq()
    } catch (err) {
      toast.error('Error', err.message)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="glass-card p-5">
        <div className="mb-5 flex items-center gap-2">
          <Clock className="h-5 w-5 text-indigo-600" />
          <h3 className="font-semibold text-slate-900">Línea de tiempo</h3>
        </div>
        {loading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : items.length === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 px-4 py-8 text-center text-sm text-slate-500">
            Aún no hay entradas en la bitácora de este expediente.
          </p>
        ) : (
          <ol className="relative border-l-2 border-indigo-200 pl-6">
            {items.map((entry) => (
              <li key={entry.id_bitacora} className="mb-6 last:mb-0">
                <span className="absolute -left-[7px] mt-1.5 h-3 w-3 rounded-full border-2 border-white bg-indigo-500 shadow-sm shadow-indigo-500/30" />
                <time className="text-xs font-medium text-slate-400">{entry.fecha_hora}</time>
                <p className="mt-1 text-sm font-semibold text-slate-900">{entry.autor_nombre}</p>
                <p className="mt-0.5 text-sm leading-relaxed text-slate-700">{entry.nota}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <span className="status-badge status-badge--neutral">
                    Avance {entry.avance_pct}%
                  </span>
                  <span className="status-badge status-badge--active">{entry.estado_caso}</span>
                </div>
              </li>
            ))}
          </ol>
        )}
      </Card>

      <Card className="glass-card p-5">
        <div className="mb-5 flex items-center gap-2">
          <PenLine className="h-5 w-5 text-indigo-600" />
          <h3 className="font-semibold text-slate-900">Registrar avance</h3>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <label className="block text-sm font-medium text-slate-700">
            Avance de investigación: <span className="text-indigo-600">{avance}%</span>
            <input
              type="range"
              min={0}
              max={100}
              value={avance}
              onChange={(e) => setAvance(Number(e.target.value))}
              className="mt-2 w-full accent-indigo-600"
            />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Estado del caso
            <select
              value={estado}
              onChange={(e) => setEstado(e.target.value)}
              className="input-field mt-1.5"
            >
              {ESTADOS.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>

          {isClosing && req && (
            <div
              className={`rounded-xl border px-4 py-3 ${
                req.ok
                  ? 'border-emerald-200 bg-emerald-50/60'
                  : 'border-amber-200 bg-amber-50/60'
              }`}
            >
              <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-800">
                <Lock className="h-4 w-4" />
                Requisitos de cierre (RN-09)
              </div>
              <ul className="space-y-1.5">
                {Object.entries(CHECK_LABELS).map(([key, label]) => {
                  const ok = req.checks?.[key]
                  return (
                    <li key={key} className="flex items-center gap-2 text-xs text-slate-700">
                      {ok ? (
                        <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                      ) : (
                        <XCircle className="h-4 w-4 shrink-0 text-rose-500" />
                      )}
                      <span className={ok ? '' : 'text-slate-600'}>{label}</span>
                    </li>
                  )
                })}
              </ul>
              {!req.ok && (
                <p className="mt-2 text-xs font-medium text-amber-700">
                  Completa los pendientes para poder cerrar el expediente.
                </p>
              )}
            </div>
          )}

          <label className="block text-sm font-medium text-slate-700">
            Nota de bitácora
            <textarea
              required
              value={nota}
              onChange={(e) => setNota(e.target.value)}
              rows={4}
              className="input-field mt-1.5"
              placeholder="Diligencias realizadas, hallazgos, próximos pasos…"
            />
          </label>

          <Button type="submit" disabled={isClosing && req && !req.ok}>
            Agregar a bitácora
          </Button>
        </form>
      </Card>
    </div>
  )
}
