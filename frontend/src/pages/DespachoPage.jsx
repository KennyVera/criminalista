import { useCallback, useEffect, useMemo, useState } from 'react'
import { Navigate } from 'react-router-dom'
import {
  Radio,
  Plus,
  Send,
  MapPin,
  AlertTriangle,
  X,
  CheckCircle2,
  Undo2,
  LifeBuoy,
  FileText,
} from 'lucide-react'
import { patrullasApi } from '../api/patrullas'
import { Badge, Button, Card, Input, Select, Spinner } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { canDespachar } from '../utils/roles'

const PRIO_TONE = { Alta: 'danger', Media: 'warning', Baja: 'neutral' }
const ESTADO_TONE = {
  Reportado: 'info',
  Despachado: 'warning',
  'En camino': 'warning',
  'En el lugar': 'blue',
  'En atención': 'blue',
  Atendido: 'green',
  Cerrado: 'neutral',
}

export default function DespachoPage() {
  const { user } = useAuth()
  const toast = useToast()
  const allowed = canDespachar(user)

  const [incidentes, setIncidentes] = useState([])
  const [patrullas, setPatrullas] = useState([])
  const [catalogos, setCatalogos] = useState({ tipos_incidente: [], prioridades: [] })
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({
    tipo: 'Robo',
    ubicacion: '',
    descripcion: '',
    prioridad: 'Media',
    reportante: '',
  })
  const [creating, setCreating] = useState(false)
  const [dispatchTarget, setDispatchTarget] = useState(null)
  const [patrullaSel, setPatrullaSel] = useState('')
  const [prioridadSel, setPrioridadSel] = useState('Media')
  const [notas, setNotas] = useState('')
  const [dispatching, setDispatching] = useState(false)
  const [parteTarget, setParteTarget] = useState(null)
  const [returnTarget, setReturnTarget] = useState(null)
  const [motivo, setMotivo] = useState('')
  const [acting, setActing] = useState(false)

  const load = useCallback(async () => {
    try {
      const [inc, pats] = await Promise.all([
        patrullasApi.listarIncidentes(),
        patrullasApi.listar(),
      ])
      setIncidentes(inc.items || [])
      setPatrullas(pats.items || [])
    } catch (err) {
      toast.error('Despacho', err.message)
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    if (!allowed) return
    patrullasApi.catalogos().then(setCatalogos).catch(() => {})
    load()
  }, [allowed, load])

  const patrullasDisponibles = useMemo(
    () => patrullas.filter((p) => p.estado === 'Disponible' && p.total_oficiales > 0),
    [patrullas],
  )

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!form.ubicacion.trim()) {
      toast.error('Ubicación requerida', 'Indique dónde ocurre el incidente.')
      return
    }
    setCreating(true)
    try {
      await patrullasApi.crearIncidente(form)
      toast.success('Incidente registrado', `${form.tipo} · ${form.ubicacion}`)
      setForm((f) => ({ ...f, ubicacion: '', descripcion: '', reportante: '' }))
      load()
    } catch (err) {
      toast.error('No se pudo registrar', err.message)
    } finally {
      setCreating(false)
    }
  }

  const openDispatch = (inc) => {
    setDispatchTarget(inc)
    setPatrullaSel('')
    setPrioridadSel(inc.prioridad || 'Media')
    setNotas('')
  }

  const handleDispatch = async () => {
    if (!patrullaSel) {
      toast.error('Seleccione patrulla', 'Elija una patrulla disponible.')
      return
    }
    setDispatching(true)
    try {
      const inc = await patrullasApi.despachar(dispatchTarget.id_incidente, {
        fk_patrulla: Number(patrullaSel),
        prioridad: prioridadSel,
        notas,
      })
      toast.success('Patrulla despachada', `${inc.patrulla_codigo} → ${inc.codigo}`)
      setDispatchTarget(null)
      load()
    } catch (err) {
      toast.error('No se pudo despachar', err.message)
    } finally {
      setDispatching(false)
    }
  }

  const aprobar = async (inc) => {
    if (!window.confirm(`¿Aprobar el cierre del incidente ${inc.codigo}?`)) return
    setActing(true)
    try {
      await patrullasApi.cerrarIncidente(inc.id_incidente)
      toast.success('Cierre aprobado', inc.codigo)
      setParteTarget(null)
      load()
    } catch (err) {
      toast.error('No se pudo cerrar', err.message)
    } finally {
      setActing(false)
    }
  }

  const handleReturn = async () => {
    if (!motivo.trim()) {
      toast.error('Motivo requerido', 'Indique por qué se devuelve el caso.')
      return
    }
    setActing(true)
    try {
      await patrullasApi.devolverIncidente(returnTarget.id_incidente, { motivo })
      toast.success('Caso devuelto', 'El oficial deberá corregirlo.')
      setReturnTarget(null)
      setMotivo('')
      load()
    } catch (err) {
      toast.error('No se pudo devolver', err.message)
    } finally {
      setActing(false)
    }
  }

  if (!allowed) return <Navigate to="/" replace />

  const tipos = catalogos.tipos_incidente.length
    ? catalogos.tipos_incidente
    : ['Robo', 'Hurto', 'Disturbio', 'Otro']
  const prioridades = catalogos.prioridades.length
    ? catalogos.prioridades
    : ['Alta', 'Media', 'Baja']

  return (
    <section className="mx-auto max-w-7xl space-y-8">
      <header className="page-header">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-gradient-to-br from-indigo-600 to-blue-700 p-3 text-white shadow-lg shadow-indigo-500/25">
            <Radio className="h-6 w-6" />
          </div>
          <div>
            <h2>Central de Despacho</h2>
            <p>
              Evalúe los incidentes, defina la prioridad, despache la patrulla y supervise el cierre
              (CU-O78). El despacho y el cierre son responsabilidad del Comisario.
            </p>
          </div>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        <Card className="glass-card h-fit p-5">
          <div className="mb-5 flex items-center gap-2">
            <Plus className="h-5 w-5 text-indigo-600" />
            <h3 className="font-semibold text-slate-900">Registrar incidente</h3>
          </div>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block text-sm font-medium text-slate-700">
                Tipo
                <Select
                  value={form.tipo}
                  onChange={(e) => setForm((f) => ({ ...f, tipo: e.target.value }))}
                  className="mt-1.5"
                >
                  {tipos.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </Select>
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Prioridad preliminar
                <Select
                  value={form.prioridad}
                  onChange={(e) => setForm((f) => ({ ...f, prioridad: e.target.value }))}
                  className="mt-1.5"
                >
                  {prioridades.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </Select>
              </label>
            </div>
            <label className="block text-sm font-medium text-slate-700">
              Ubicación
              <Input
                value={form.ubicacion}
                onChange={(e) => setForm((f) => ({ ...f, ubicacion: e.target.value }))}
                className="mt-1.5"
                placeholder="Ej. Av. Principal y Calle 5"
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Reportante (opcional)
              <Input
                value={form.reportante}
                onChange={(e) => setForm((f) => ({ ...f, reportante: e.target.value }))}
                className="mt-1.5"
                placeholder="Ciudadano, línea 911…"
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Descripción (opcional)
              <textarea
                value={form.descripcion}
                onChange={(e) => setForm((f) => ({ ...f, descripcion: e.target.value }))}
                rows={3}
                className="input-field mt-1.5"
                placeholder="Detalle del incidente…"
              />
            </label>
            <Button type="submit" disabled={creating}>
              <Plus className="h-4 w-4" />
              {creating ? 'Registrando…' : 'Registrar incidente'}
            </Button>
          </form>
        </Card>

        <div className="space-y-4">
          {loading ? (
            <div className="flex justify-center py-12">
              <Spinner />
            </div>
          ) : incidentes.length === 0 ? (
            <Card className="glass-card p-8 text-center text-sm text-slate-500">
              No hay incidentes registrados.
            </Card>
          ) : (
            incidentes.map((inc) => (
              <Card key={inc.id_incidente} className="glass-card p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-sm font-semibold text-indigo-700">
                        {inc.codigo}
                      </span>
                      <Badge tone={ESTADO_TONE[inc.estado] || 'neutral'}>{inc.estado}</Badge>
                      <Badge tone={PRIO_TONE[inc.prioridad] || 'neutral'}>
                        <AlertTriangle className="mr-1 inline h-3 w-3" />
                        {inc.prioridad}
                      </Badge>
                      {inc.apoyo_solicitado && (
                        <Badge tone="danger">
                          <LifeBuoy className="mr-1 inline h-3 w-3" />
                          Apoyo solicitado
                        </Badge>
                      )}
                    </div>
                    <p className="mt-1.5 font-medium text-slate-800">{inc.tipo}</p>
                    <div className="mt-0.5 flex items-center gap-1 text-sm text-slate-600">
                      <MapPin className="h-3.5 w-3.5 text-slate-400" /> {inc.ubicacion}
                    </div>
                    {inc.descripcion && (
                      <p className="mt-1 text-sm text-slate-500">{inc.descripcion}</p>
                    )}
                    {inc.patrulla_codigo && (
                      <p className="mt-1.5 text-xs text-slate-500">
                        Patrulla asignada:{' '}
                        <span className="font-mono font-semibold text-slate-700">
                          {inc.patrulla_codigo}
                        </span>
                      </p>
                    )}
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-2">
                    {inc.estado === 'Reportado' && (
                      <Button onClick={() => openDispatch(inc)}>
                        <Send className="h-4 w-4" />
                        Despachar
                      </Button>
                    )}
                    {inc.estado === 'Atendido' && (
                      <>
                        <Button variant="secondary" onClick={() => setParteTarget(inc)}>
                          <FileText className="h-4 w-4" />
                          Revisar parte
                        </Button>
                        <div className="flex gap-2">
                          <Button onClick={() => aprobar(inc)} disabled={acting}>
                            <CheckCircle2 className="h-4 w-4" />
                            Aprobar cierre
                          </Button>
                          <Button variant="danger" onClick={() => setReturnTarget(inc)}>
                            <Undo2 className="h-4 w-4" />
                            Devolver
                          </Button>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>

      {dispatchTarget && (
        <Modal title={`Despachar · ${dispatchTarget.codigo}`} onClose={() => setDispatchTarget(null)}>
          {patrullasDisponibles.length === 0 ? (
            <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/60 px-4 py-6 text-center text-sm text-slate-500">
              No hay patrullas disponibles con oficiales asignados.
            </p>
          ) : (
            <div className="space-y-4">
              <label className="block text-sm font-medium text-slate-700">
                Prioridad definitiva
                <Select
                  value={prioridadSel}
                  onChange={(e) => setPrioridadSel(e.target.value)}
                  className="mt-1.5"
                >
                  {prioridades.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </Select>
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Patrulla disponible
                <Select
                  value={patrullaSel}
                  onChange={(e) => setPatrullaSel(e.target.value)}
                  className="mt-1.5"
                >
                  <option value="">Seleccione…</option>
                  {patrullasDisponibles.map((p) => (
                    <option key={p.id_patrulla} value={p.id_patrulla}>
                      {p.codigo} · {p.sector} ({p.total_oficiales} of.)
                    </option>
                  ))}
                </Select>
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Instrucciones (opcional)
                <textarea
                  value={notas}
                  onChange={(e) => setNotas(e.target.value)}
                  rows={2}
                  className="input-field mt-1.5"
                  placeholder="Indicaciones para la patrulla…"
                />
              </label>
            </div>
          )}
          <div className="mt-5 flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setDispatchTarget(null)}>
              Cancelar
            </Button>
            <Button onClick={handleDispatch} disabled={dispatching || !patrullaSel}>
              <Send className="h-4 w-4" />
              {dispatching ? 'Despachando…' : 'Despachar'}
            </Button>
          </div>
        </Modal>
      )}

      {parteTarget && (
        <Modal title={`Parte policial · ${parteTarget.codigo}`} onClose={() => setParteTarget(null)}>
          <div className="space-y-3 text-sm">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Resultado de la atención
              </p>
              <p className="mt-1 text-slate-700">{parteTarget.resultado_atencion || '—'}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Parte</p>
              <pre className="mt-1 whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-xs text-slate-700">
                {parteTarget.parte_policial || '—'}
              </pre>
            </div>
          </div>
          <div className="mt-5 flex justify-end gap-2">
            <Button variant="danger" onClick={() => { setReturnTarget(parteTarget); setParteTarget(null) }}>
              <Undo2 className="h-4 w-4" />
              Devolver
            </Button>
            <Button onClick={() => aprobar(parteTarget)} disabled={acting}>
              <CheckCircle2 className="h-4 w-4" />
              Aprobar cierre
            </Button>
          </div>
        </Modal>
      )}

      {returnTarget && (
        <Modal title={`Devolver · ${returnTarget.codigo}`} onClose={() => setReturnTarget(null)}>
          <label className="block text-sm font-medium text-slate-700">
            Motivo de la devolución
            <textarea
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              rows={3}
              className="input-field mt-1.5"
              placeholder="Indique qué debe corregir el oficial…"
            />
          </label>
          <div className="mt-5 flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setReturnTarget(null)}>
              Cancelar
            </Button>
            <Button variant="danger" onClick={handleReturn} disabled={acting}>
              <Undo2 className="h-4 w-4" />
              Devolver para corrección
            </Button>
          </div>
        </Modal>
      )}
    </section>
  )
}

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm">
      <Card className="glass-card w-full max-w-md p-5">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-semibold text-slate-900">{title}</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        {children}
      </Card>
    </div>
  )
}
