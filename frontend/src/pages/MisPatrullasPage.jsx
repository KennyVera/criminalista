import { useCallback, useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import {
  ShieldCheck,
  MapPin,
  Clock,
  Users,
  Navigation,
  AlertTriangle,
  Plus,
  LifeBuoy,
  FileCheck2,
  FileText,
  X,
} from 'lucide-react'
import { patrullasApi } from '../api/patrullas'
import { Badge, Button, Card, Input, Select, Spinner } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { isOficial } from '../utils/roles'

const ESTADO_TONE = {
  Disponible: 'green',
  Despachada: 'warning',
  'En ruta': 'warning',
  'En sitio': 'blue',
  'En camino': 'warning',
  'En el lugar': 'blue',
  'En atención': 'blue',
  Atendido: 'green',
  Reportado: 'info',
  Despachado: 'warning',
  Cerrado: 'neutral',
}
const PRIO_TONE = { Alta: 'danger', Media: 'warning', Baja: 'neutral' }

// Acción de avance lineal que ofrece el oficial según el estado del incidente.
const SIGUIENTE_ACCION = {
  Despachado: 'Aceptar y salir (en camino)',
  'En camino': 'Marcar llegada al lugar',
  'En el lugar': 'Iniciar atención',
}

export default function MisPatrullasPage() {
  const { user } = useAuth()
  const toast = useToast()
  const allowed = isOficial(user)

  const [patrullas, setPatrullas] = useState([])
  const [incidentes, setIncidentes] = useState([])
  const [catalogos, setCatalogos] = useState({ tipos_incidente: [], prioridades: [] })
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(null)
  const [form, setForm] = useState({
    tipo: 'Robo',
    direccion: '',
    descripcion: '',
    prioridad: 'Media',
    reportante: '',
  })
  const [creating, setCreating] = useState(false)
  const [finalizarTarget, setFinalizarTarget] = useState(null)
  const [resultado, setResultado] = useState('')
  const [parte, setParte] = useState('')

  const load = useCallback(async () => {
    try {
      const res = await patrullasApi.misPatrullas()
      setPatrullas(res.patrullas || [])
      setIncidentes(res.incidentes || [])
    } catch (err) {
      toast.error('Mis patrullas', err.message)
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    if (!allowed) return
    patrullasApi.catalogos().then(setCatalogos).catch(() => {})
    load()
  }, [allowed, load])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!form.direccion.trim()) {
      toast.error('Ubicación requerida', 'Indique la dirección del incidente.')
      return
    }
    setCreating(true)
    try {
      await patrullasApi.crearIncidente(form)
      toast.success('Incidente registrado', 'El comisario lo evaluará y despachará.')
      setForm((f) => ({ ...f, direccion: '', descripcion: '', reportante: '' }))
      load()
    } catch (err) {
      toast.error('No se pudo registrar', err.message)
    } finally {
      setCreating(false)
    }
  }

  const avanzar = async (inc) => {
    setBusy(inc.id_incidente)
    try {
      const updated = await patrullasApi.avanzarIncidente(inc.id_incidente, {})
      toast.success('Incidente actualizado', `${updated.codigo} → ${updated.estado}`)
      load()
    } catch (err) {
      toast.error('No se pudo actualizar', err.message)
    } finally {
      setBusy(null)
    }
  }

  const apoyo = async (inc) => {
    setBusy(inc.id_incidente)
    try {
      await patrullasApi.solicitarApoyo(inc.id_incidente, {})
      toast.success('Apoyo solicitado', `Se notificó el apoyo para ${inc.codigo}`)
      load()
    } catch (err) {
      toast.error('No se pudo solicitar', err.message)
    } finally {
      setBusy(null)
    }
  }

  const openFinalizar = (inc) => {
    setFinalizarTarget(inc)
    setResultado('')
    setParte('')
  }

  const handleFinalizar = async () => {
    if (!resultado.trim()) {
      toast.error('Resultado requerido', 'Describa el resultado de la atención.')
      return
    }
    setBusy(finalizarTarget.id_incidente)
    try {
      await patrullasApi.finalizarIncidente(finalizarTarget.id_incidente, { resultado, parte })
      toast.success('Atención finalizada', 'El comisario revisará el parte.')
      setFinalizarTarget(null)
      load()
    } catch (err) {
      toast.error('No se pudo finalizar', err.message)
    } finally {
      setBusy(null)
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
    <section className="mx-auto max-w-6xl space-y-8">
      <header className="page-header">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-gradient-to-br from-indigo-600 to-blue-700 p-3 text-white shadow-lg shadow-indigo-500/25">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <h2>Mis patrullas</h2>
            <p>
              Reporte incidentes, reciba y atienda los despachos del comisario, y genere el parte
              policial (CU-O78).
            </p>
          </div>
        </div>
      </header>

      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      ) : (
        <>
          <Card className="glass-card p-5">
            <div className="mb-5 flex items-center gap-2">
              <Plus className="h-5 w-5 text-indigo-600" />
              <h3 className="font-semibold text-slate-900">Reportar incidente</h3>
            </div>
            <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2">
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
              <label className="block text-sm font-medium text-slate-700 sm:col-span-2">
                Ubicación
                <Input
                  value={form.direccion}
                  onChange={(e) => setForm((f) => ({ ...f, direccion: e.target.value }))}
                  className="mt-1.5"
                  placeholder="Ej. Av. Principal y Calle 5"
                />
              </label>
              <label className="block text-sm font-medium text-slate-700 sm:col-span-2">
                Descripción (opcional)
                <textarea
                  value={form.descripcion}
                  onChange={(e) => setForm((f) => ({ ...f, descripcion: e.target.value }))}
                  rows={2}
                  className="input-field mt-1.5"
                  placeholder="Detalle del incidente…"
                />
              </label>
              <div className="sm:col-span-2">
                <Button type="submit" disabled={creating}>
                  <Plus className="h-4 w-4" />
                  {creating ? 'Registrando…' : 'Reportar incidente'}
                </Button>
              </div>
            </form>
          </Card>

          <div>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Patrullas asignadas
            </h3>
            {patrullas.length === 0 ? (
              <Card className="glass-card p-8 text-center text-sm text-slate-500">
                No está asignado a ninguna patrulla por el momento.
              </Card>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {patrullas.map((p) => (
                  <Card key={p.id_patrulla} className="glass-card p-5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-semibold text-indigo-700">
                        {p.codigo}
                      </span>
                      <Badge tone={ESTADO_TONE[p.estado] || 'neutral'}>{p.estado}</Badge>
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-600">
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5 text-slate-400" /> {p.sector}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5 text-slate-400" /> {p.turno}
                      </span>
                    </div>
                    <div className="mt-3 flex items-center gap-1.5 text-xs text-slate-500">
                      <Users className="h-3.5 w-3.5" />
                      {(p.oficiales || []).map((o) => o.oficial_nombre).join(', ') || 'Sin oficiales'}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>

          <div>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Incidentes asignados
            </h3>
            {incidentes.length === 0 ? (
              <Card className="glass-card p-8 text-center text-sm text-slate-500">
                No tiene incidentes despachados pendientes.
              </Card>
            ) : (
              <div className="space-y-4">
                {incidentes.map((inc) => (
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
                          {inc.expediente_case_number && (
                            <Badge tone="info">
                              <FileText className="mr-1 inline h-3 w-3" />
                              Expediente {inc.expediente_case_number}
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
                        {inc.motivo_devolucion && (
                          <p className="mt-2 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">
                            Devuelto por el comisario: {inc.motivo_devolucion}
                          </p>
                        )}
                        {inc.estado === 'Atendido' && (
                          <p className="mt-2 text-xs text-slate-500">
                            En revisión del comisario.
                          </p>
                        )}
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-2">
                        {SIGUIENTE_ACCION[inc.estado] && (
                          <Button onClick={() => avanzar(inc)} disabled={busy === inc.id_incidente}>
                            <Navigation className="h-4 w-4" />
                            {busy === inc.id_incidente ? 'Actualizando…' : SIGUIENTE_ACCION[inc.estado]}
                          </Button>
                        )}
                        {inc.estado === 'En atención' && (
                          <Button onClick={() => openFinalizar(inc)} disabled={busy === inc.id_incidente}>
                            <FileCheck2 className="h-4 w-4" />
                            Finalizar atención
                          </Button>
                        )}
                        {inc.estado !== 'Atendido' && inc.estado !== 'Cerrado' && (
                          <Button
                            variant="secondary"
                            onClick={() => apoyo(inc)}
                            disabled={busy === inc.id_incidente || inc.apoyo_solicitado}
                          >
                            <LifeBuoy className="h-4 w-4" />
                            {inc.apoyo_solicitado ? 'Apoyo solicitado' : 'Solicitar apoyo'}
                          </Button>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {finalizarTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm">
          <Card className="glass-card w-full max-w-lg p-5">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-semibold text-slate-900">
                Finalizar atención · {finalizarTarget.codigo}
              </h3>
              <button
                type="button"
                onClick={() => setFinalizarTarget(null)}
                className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4">
              <label className="block text-sm font-medium text-slate-700">
                Resultado de la atención
                <textarea
                  value={resultado}
                  onChange={(e) => setResultado(e.target.value)}
                  rows={3}
                  className="input-field mt-1.5"
                  placeholder="Describa lo actuado, involucrados, evidencias recolectadas…"
                />
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Parte policial (opcional)
                <textarea
                  value={parte}
                  onChange={(e) => setParte(e.target.value)}
                  rows={4}
                  className="input-field mt-1.5"
                  placeholder="Si lo deja vacío se generará un parte con los datos del incidente."
                />
              </label>
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setFinalizarTarget(null)}>
                Cancelar
              </Button>
              <Button onClick={handleFinalizar} disabled={busy === finalizarTarget.id_incidente}>
                <FileCheck2 className="h-4 w-4" />
                Finalizar y generar parte
              </Button>
            </div>
          </Card>
        </div>
      )}
    </section>
  )
}
