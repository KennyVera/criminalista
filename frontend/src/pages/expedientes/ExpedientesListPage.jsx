import { useCallback, useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import {
  FileText,
  Plus,
  Search,
  Eye,
  Pencil,
  Lock,
  RotateCcw,
  Archive,
  Trash2,
  X,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Link2,
  MapPin,
} from 'lucide-react'
import { expedientesApi } from '../../api/expedientes'
import { Badge, Button, Card, Input, Select, Spinner, EmptyState } from '../../components/ui'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../../context/ToastContext'
import {
  canViewExpedientes,
  canRegisterExpediente,
  canEditExpediente,
  canManageExpedienteLifecycle,
} from '../../utils/roles'

const TIPOS_DELITO = [
  'Robo',
  'Hurto',
  'Homicidio',
  'Asesinato',
  'Violencia intrafamiliar',
  'Estafa',
  'Secuestro',
  'Narcotráfico',
  'Daño a la propiedad',
  'Lesiones',
  'Otro',
]

const PRIORIDADES = ['Alta', 'Media', 'Baja']

// Catálogo de códigos IUCR por tipo de delito (ayuda a quien no recuerda el código).
const IUCR_POR_DELITO = {
  Robo: [
    { iucr: '031A', fbi: '03', label: '031A — Robo a mano armada (arma de fuego)' },
    { iucr: '0320', fbi: '03', label: '0320 — Robo con fuerza, sin arma' },
    { iucr: '033A', fbi: '03', label: '033A — Robo con intimidación' },
  ],
  Hurto: [
    { iucr: '0820', fbi: '06', label: '0820 — Hurto $500 o menos' },
    { iucr: '0810', fbi: '06', label: '0810 — Hurto mayor a $500' },
    { iucr: '0860', fbi: '06', label: '0860 — Hurto en comercio (retail)' },
  ],
  Homicidio: [
    { iucr: '0110', fbi: '01A', label: '0110 — Homicidio doloso (1er grado)' },
    { iucr: '0142', fbi: '01B', label: '0142 — Homicidio involuntario' },
  ],
  Asesinato: [
    { iucr: '0110', fbi: '01A', label: '0110 — Asesinato (homicidio 1er grado)' },
    { iucr: '0130', fbi: '01A', label: '0130 — Homicidio 2do grado' },
  ],
  'Violencia intrafamiliar': [
    { iucr: '0486', fbi: '08B', label: '0486 — Agresión doméstica simple' },
    { iucr: '0488', fbi: '08B', label: '0488 — Agresión doméstica agravada' },
  ],
  Estafa: [
    { iucr: '1110', fbi: '11', label: '1110 — Práctica engañosa (cheque sin fondos)' },
    { iucr: '1130', fbi: '11', label: '1130 — Fraude financiero' },
    { iucr: '1150', fbi: '11', label: '1150 — Estafa por confianza' },
  ],
  Secuestro: [
    { iucr: '1710', fbi: '20', label: '1710 — Secuestro' },
    { iucr: '1715', fbi: '20', label: '1715 — Sustracción de menor' },
  ],
  'Narcotráfico': [
    { iucr: '2010', fbi: '18', label: '2010 — Fabricación/entrega de narcóticos' },
    { iucr: '2020', fbi: '18', label: '2020 — Posesión de narcóticos' },
  ],
  'Daño a la propiedad': [
    { iucr: '1310', fbi: '14', label: '1310 — Daño a la propiedad' },
    { iucr: '1320', fbi: '14', label: '1320 — Daño a vehículo' },
  ],
  Lesiones: [
    { iucr: '041A', fbi: '04B', label: '041A — Agresión agravada con arma' },
    { iucr: '0460', fbi: '08B', label: '0460 — Agresión simple (lesiones)' },
    { iucr: '0560', fbi: '08A', label: '0560 — Asalto simple' },
  ],
  Otro: [],
}

const SI_NO = ['Sí', 'No']

const ESTADO_TONE = {
  // Ciclo de vida del expediente (registro manual)
  ACTIVO: 'green',
  REABIERTO: 'blue',
  CERRADO: 'warning',
  ARCHIVADO: 'neutral',
  ELIMINADO: 'danger',
  // Estado del caso (dataset existente)
  Abierto: 'green',
  'En investigación': 'blue',
  Resuelto: 'green',
  Cerrado: 'warning',
  Archivado: 'neutral',
  Importado: 'neutral',
}

const ESTADO_EDITABLE = (estado) =>
  String(estado || '').toUpperCase() === 'ACTIVO' ||
  String(estado || '').toUpperCase() === 'REABIERTO'

function hoyISO() {
  const d = new Date()
  const off = d.getTimezoneOffset()
  return new Date(d.getTime() - off * 60000).toISOString().slice(0, 10)
}

function field(form, setForm, key) {
  return {
    value: form[key] ?? '',
    onChange: (e) => setForm((f) => ({ ...f, [key]: e.target.value })),
  }
}

function ModalShell({ title, onClose, children, icon: Icon }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm">
      <Card className="glass-card max-h-[88vh] w-full max-w-lg overflow-y-auto p-5">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="flex items-center gap-2 font-semibold text-slate-900">
            {Icon && <Icon className="h-5 w-5 text-indigo-600" />}
            {title}
          </h3>
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

export default function ExpedientesListPage() {
  const { user } = useAuth()
  const toast = useToast()
  const allowed = canViewExpedientes(user)
  const puedeRegistrar = canRegisterExpediente(user)
  const puedeEditar = canEditExpediente(user)
  const puedeLifecycle = canManageExpedienteLifecycle(user)

  const [data, setData] = useState({ items: [], totalItems: 0, totalPages: 1, page: 1 })
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [estado, setEstado] = useState('')
  const [page, setPage] = useState(1)

  const [showRegister, setShowRegister] = useState(false)
  const [editTarget, setEditTarget] = useState(null)
  const [estadoTarget, setEstadoTarget] = useState(null)
  const [distritos, setDistritos] = useState([])

  useEffect(() => {
    if (!allowed) return
    expedientesApi
      .catalogos()
      .then((res) => setDistritos(res.distritos || []))
      .catch(() => setDistritos([]))
  }, [allowed])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await expedientesApi.listar({ q, estado, page, per_page: 10 })
      setData(res)
    } catch (err) {
      toast.error('Expedientes', err.message)
    } finally {
      setLoading(false)
    }
  }, [q, estado, page, toast])

  useEffect(() => {
    if (allowed) load()
  }, [allowed, load])

  const estadoFiltros = [
    { id: '', label: 'Todos' },
    { id: 'Abierto', label: 'Abiertos' },
    { id: 'En investigación', label: 'En investigación' },
    { id: 'Cerrado', label: 'Cerrados' },
    { id: 'Archivado', label: 'Archivados' },
  ]

  if (!allowed) return <Navigate to="/" replace />

  const onSearchSubmit = (e) => {
    e.preventDefault()
    setPage(1)
    load()
  }

  const refreshAfterMutation = () => {
    load()
  }

  return (
    <section className="mx-auto max-w-7xl space-y-6">
      <header className="page-header">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="rounded-xl bg-gradient-to-br from-indigo-600 to-blue-700 p-3 text-white shadow-lg shadow-indigo-500/25">
              <FileText className="h-6 w-6" />
            </div>
            <div>
              <h2>Expedientes criminales</h2>
              <p>
                Registre, consulte y gestione el ciclo de vida de los expedientes
                (activo, cerrado, reabierto, archivado y eliminación lógica).
              </p>
            </div>
          </div>
          {puedeRegistrar && (
            <Button onClick={() => setShowRegister(true)}>
              <Plus className="h-4 w-4" />
              Registrar expediente
            </Button>
          )}
        </div>
      </header>

      <Card className="glass-card p-4">
        <form onSubmit={onSearchSubmit} className="flex flex-wrap items-center gap-3">
          <div className="relative min-w-[240px] flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              className="pl-9"
              placeholder="Buscar por número de caso…"
            />
          </div>
          <Button type="submit" variant="secondary">
            <Search className="h-4 w-4" />
            Buscar
          </Button>
        </form>

        <div className="mt-3 flex flex-wrap gap-2">
          {estadoFiltros.map((f) => (
            <button
              key={f.id || 'all'}
              type="button"
              onClick={() => {
                setEstado(f.id)
                setPage(1)
              }}
              className={
                'rounded-full px-3.5 py-1.5 text-sm font-semibold transition ' +
                (estado === f.id
                  ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow'
                  : 'border border-slate-200 bg-white/70 text-slate-600 hover:border-indigo-300')
              }
            >
              {f.label}
            </button>
          ))}
        </div>
      </Card>

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : data.items.length === 0 ? (
        <Card className="glass-card">
          <EmptyState
            icon={FileText}
            title="Sin expedientes"
            description={data.message || 'No hay expedientes que coincidan con la búsqueda.'}
            action={
              puedeRegistrar && (
                <Button onClick={() => setShowRegister(true)}>
                  <Plus className="h-4 w-4" />
                  Registrar el primero
                </Button>
              )
            }
          />
        </Card>
      ) : (
        <Card className="glass-card" flush>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <th className="px-4 py-3">Nº de caso</th>
                  <th className="px-4 py-3">Tipo de delito</th>
                  <th className="px-4 py-3">Distrito</th>
                  <th className="px-4 py-3">Fecha del hecho</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3">Prioridad</th>
                  <th className="px-4 py-3">Detective</th>
                  <th className="px-4 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((exp) => {
                  const est = exp.estado || '—'
                  const editable = ESTADO_EDITABLE(exp.estado) && exp.es_expediente
                  return (
                    <tr
                      key={exp.case_number}
                      className="border-b border-slate-50 transition hover:bg-indigo-50/30"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-semibold text-indigo-700">
                            {exp.case_number}
                          </span>
                          {exp.es_expediente && (
                            <span className="rounded-md bg-indigo-50 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-indigo-600">
                              Expediente
                            </span>
                          )}
                        </div>
                        {exp.titulo && (
                          <p className="mt-0.5 max-w-[220px] truncate text-xs text-slate-400">
                            {exp.titulo}
                          </p>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-600">{exp.tipo_delito || '—'}</td>
                      <td className="px-4 py-3 text-slate-600">
                        {exp.distrito ? `Distrito ${exp.distrito}`.replace('Distrito Distrito', 'Distrito') : '—'}
                      </td>
                      <td className="px-4 py-3 text-slate-600">{exp.fecha || '—'}</td>
                      <td className="px-4 py-3">
                        <Badge tone={ESTADO_TONE[est] || 'neutral'}>{est}</Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-600">{exp.prioridad || '—'}</td>
                      <td className="px-4 py-3 text-slate-600">{exp.detective || 'Sin asignar'}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <Link
                            to={`/expedientes/${encodeURIComponent(exp.case_number)}`}
                            title="Ver / consultar"
                            className="rounded-lg p-1.5 text-slate-500 transition hover:bg-indigo-50 hover:text-indigo-700"
                          >
                            <Eye className="h-4 w-4" />
                          </Link>
                          {puedeEditar && editable && (
                            <button
                              type="button"
                              title="Editar"
                              onClick={() => setEditTarget(exp)}
                              className="rounded-lg p-1.5 text-slate-500 transition hover:bg-indigo-50 hover:text-indigo-700"
                            >
                              <Pencil className="h-4 w-4" />
                            </button>
                          )}
                          {puedeEditar && editable && (
                            <button
                              type="button"
                              title="Cerrar expediente"
                              onClick={() => setEstadoTarget({ exp, accion: 'cerrar' })}
                              className="rounded-lg p-1.5 text-amber-600 transition hover:bg-amber-50"
                            >
                              <Lock className="h-4 w-4" />
                            </button>
                          )}
                          {puedeLifecycle && exp.es_expediente && est === 'CERRADO' && (
                            <button
                              type="button"
                              title="Reabrir"
                              onClick={() => setEstadoTarget({ exp, accion: 'reabrir' })}
                              className="rounded-lg p-1.5 text-blue-600 transition hover:bg-blue-50"
                            >
                              <RotateCcw className="h-4 w-4" />
                            </button>
                          )}
                          {puedeLifecycle && exp.es_expediente && est === 'CERRADO' && (
                            <button
                              type="button"
                              title="Archivar"
                              onClick={() => setEstadoTarget({ exp, accion: 'archivar' })}
                              className="rounded-lg p-1.5 text-slate-600 transition hover:bg-slate-100"
                            >
                              <Archive className="h-4 w-4" />
                            </button>
                          )}
                          {puedeLifecycle && exp.es_expediente && est !== 'ELIMINADO' && (
                            <button
                              type="button"
                              title="Eliminar (lógico)"
                              onClick={() => setEstadoTarget({ exp, accion: 'eliminar' })}
                              className="rounded-lg p-1.5 text-rose-600 transition hover:bg-rose-50"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-sm text-slate-500">
            <span>
              {data.totalItems} expediente(s) · página {data.page} de {data.totalPages}
            </span>
            <div className="flex gap-1">
              <button
                type="button"
                disabled={data.page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 transition hover:bg-slate-50 disabled:opacity-40"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                type="button"
                disabled={data.page >= data.totalPages}
                onClick={() => setPage((p) => Math.min(data.totalPages, p + 1))}
                className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 transition hover:bg-slate-50 disabled:opacity-40"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </Card>
      )}

      {showRegister && (
        <RegisterModal
          distritos={distritos}
          onClose={() => setShowRegister(false)}
          onSaved={() => {
            setShowRegister(false)
            setPage(1)
            refreshAfterMutation()
          }}
        />
      )}

      {editTarget && (
        <EditModal
          exp={editTarget}
          distritos={distritos}
          onClose={() => setEditTarget(null)}
          onSaved={() => {
            setEditTarget(null)
            refreshAfterMutation()
          }}
        />
      )}

      {estadoTarget && (
        <EstadoModal
          exp={estadoTarget.exp}
          accion={estadoTarget.accion}
          onClose={() => setEstadoTarget(null)}
          onSaved={() => {
            setEstadoTarget(null)
            refreshAfterMutation()
          }}
        />
      )}
    </section>
  )
}

function DistritoField({ form, setForm, distritos }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      Distrito
      {distritos.length > 0 ? (
        <Select {...field(form, setForm, 'distrito')} className="mt-1.5">
          <option value="">Seleccione…</option>
          {form.distrito && !distritos.includes(form.distrito) && (
            <option value={form.distrito}>{form.distrito}</option>
          )}
          {distritos.map((d) => (
            <option key={d} value={`Distrito ${d}`}>
              Distrito {d}
            </option>
          ))}
        </Select>
      ) : (
        <Input {...field(form, setForm, 'distrito')} className="mt-1.5" placeholder="Distrito policial" />
      )}
    </label>
  )
}

function useHechoHandlers(form, setForm) {
  const iucrOptions = IUCR_POR_DELITO[form.tipo_delito] || []
  const onTipoChange = (e) =>
    setForm((f) => ({ ...f, tipo_delito: e.target.value, iucr: '', fbi_code: '' }))
  const onIucrChange = (e) => {
    const iucr = e.target.value
    const match = iucrOptions.find((o) => o.iucr === iucr)
    setForm((f) => ({ ...f, iucr, fbi_code: match ? match.fbi : f.fbi_code }))
  }
  return { iucrOptions, onTipoChange, onIucrChange }
}

function IucrFields({ form, setForm }) {
  const { iucrOptions, onIucrChange } = useHechoHandlers(form, setForm)
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <label className="block text-sm font-medium text-slate-700">
        Código IUCR
        {iucrOptions.length > 0 ? (
          <Select value={form.iucr} onChange={onIucrChange} className="mt-1.5">
            <option value="">Seleccione el código…</option>
            {iucrOptions.map((o) => (
              <option key={o.iucr} value={o.iucr}>
                {o.label}
              </option>
            ))}
          </Select>
        ) : (
          <Input
            {...field(form, setForm, 'iucr')}
            className="mt-1.5"
            placeholder={form.tipo_delito ? 'Código IUCR (manual)' : 'Elija primero el tipo de delito'}
            disabled={!form.tipo_delito}
          />
        )}
      </label>
      <label className="block text-sm font-medium text-slate-700">
        Clasificación FBI
        <Input
          {...field(form, setForm, 'fbi_code')}
          className="mt-1.5"
          placeholder="Se completa según el IUCR"
        />
      </label>
    </div>
  )
}

function HechoExtraFields({ form, setForm, distritos }) {
  return (
    <>
      <label className="block text-sm font-medium text-slate-700">
        Lugar del hecho
        <Input
          {...field(form, setForm, 'lugar_hecho')}
          className="mt-1.5"
          placeholder="Ej. Vía pública, vivienda, local comercial"
        />
      </label>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block text-sm font-medium text-slate-700">
          Ubicación / dirección
          <Input {...field(form, setForm, 'ubicacion')} className="mt-1.5" placeholder="Dirección" />
        </label>
        <DistritoField form={form} setForm={setForm} distritos={distritos} />
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <label className="block text-sm font-medium text-slate-700">
          Sector
          <Input {...field(form, setForm, 'sector')} className="mt-1.5" />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Zona
          <Input {...field(form, setForm, 'zona')} className="mt-1.5" />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Cuadra / bloque
          <Input {...field(form, setForm, 'cuadra')} className="mt-1.5" />
        </label>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block text-sm font-medium text-slate-700">
          ¿Hubo arresto?
          <Select {...field(form, setForm, 'arresto')} className="mt-1.5">
            {SI_NO.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </Select>
        </label>
        <label className="block text-sm font-medium text-slate-700">
          ¿Violencia doméstica?
          <Select {...field(form, setForm, 'violencia_domestica')} className="mt-1.5">
            {SI_NO.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </Select>
        </label>
      </div>
    </>
  )
}

function IncidentesPicker({ selected, onChange, excluirCase = '' }) {
  const [q, setQ] = useState('')
  const [results, setResults] = useState([])
  const [searching, setSearching] = useState(false)
  const selectedIds = new Set(selected.map((s) => s.id_incidente))

  const buscar = useCallback(async () => {
    setSearching(true)
    try {
      const res = await expedientesApi.buscarIncidentes({
        q,
        excluir_case: excluirCase,
        limit: 15,
      })
      setResults(res.items || [])
    } catch {
      setResults([])
    } finally {
      setSearching(false)
    }
  }, [q, excluirCase])

  useEffect(() => {
    buscar()
    // Solo en montaje: carga inicial de incidentes disponibles.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const add = (inc) => {
    if (selectedIds.has(inc.id_incidente)) return
    onChange([...selected, inc])
  }
  const remove = (id) => onChange(selected.filter((s) => s.id_incidente !== id))
  const visibles = results.filter((r) => !selectedIds.has(r.id_incidente))

  return (
    <div className="space-y-3 rounded-xl border border-indigo-100 bg-indigo-50/40 p-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-indigo-800">
        <Link2 className="h-4 w-4" /> Incidentes vinculados *
      </div>
      <p className="-mt-1 text-xs text-slate-500">
        El expediente se origina a partir de uno o varios incidentes. Busque por
        código, fecha o lugar.
      </p>

      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selected.map((s) => (
            <span
              key={s.id_incidente}
              className="inline-flex items-center gap-1 rounded-full border border-indigo-200 bg-white px-2.5 py-1 text-xs"
            >
              <span className="font-mono font-semibold text-indigo-700">{s.codigo}</span>
              <span className="text-slate-500">· {s.tipo}</span>
              <button
                type="button"
                onClick={() => remove(s.id_incidente)}
                className="ml-1 text-slate-400 transition hover:text-rose-600"
                title="Quitar"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                buscar()
              }
            }}
            className="pl-8 text-sm"
            placeholder="INC-0001, fecha o lugar…"
          />
        </div>
        <Button type="button" variant="secondary" onClick={buscar}>
          Buscar
        </Button>
      </div>

      <div className="max-h-44 space-y-1.5 overflow-y-auto">
        {searching ? (
          <p className="py-2 text-center text-xs text-slate-400">Buscando…</p>
        ) : visibles.length === 0 ? (
          <p className="py-2 text-center text-xs text-slate-400">
            No hay incidentes disponibles para vincular.
          </p>
        ) : (
          visibles.map((inc) => (
            <button
              key={inc.id_incidente}
              type="button"
              onClick={() => add(inc)}
              className="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-xs transition hover:border-indigo-300 hover:bg-indigo-50/50"
            >
              <span className="min-w-0">
                <span className="font-mono font-semibold text-indigo-700">{inc.codigo}</span>
                <span className="text-slate-600">
                  {' '}
                  · {inc.tipo} · {inc.prioridad}
                </span>
                <span className="mt-0.5 flex items-center gap-1 text-slate-400">
                  <MapPin className="h-3 w-3" />
                  {(inc.fecha_reporte || '').slice(0, 10)} — {inc.ubicacion || 's/ubicación'}
                </span>
              </span>
              <Plus className="ml-2 h-4 w-4 shrink-0 text-indigo-500" />
            </button>
          ))
        )}
      </div>
    </div>
  )
}

function RegisterModal({ onClose, onSaved, distritos = [] }) {
  const toast = useToast()
  const [form, setForm] = useState({
    case_number: '',
    titulo: '',
    tipo_delito: '',
    fecha_hecho: '',
    ubicacion: '',
    prioridad: 'Media',
    descripcion: '',
    distrito: '',
    sector: '',
    zona: '',
    cuadra: '',
    lugar_hecho: '',
    iucr: '',
    fbi_code: '',
    arresto: 'No',
    violencia_domestica: 'No',
  })
  const [similares, setSimilares] = useState([])
  const [saving, setSaving] = useState(false)
  const [incidentes, setIncidentes] = useState([])
  const { onTipoChange } = useHechoHandlers(form, setForm)

  const onIncidentesChange = (next) => {
    setIncidentes(next)
    const primero = next[0]
    if (!primero) return
    // Autocompleta los datos del hecho a partir del primer incidente (editable).
    setForm((f) => ({
      ...f,
      titulo: f.titulo || `${primero.tipo} — ${primero.ubicacion || ''}`.trim(),
      tipo_delito:
        f.tipo_delito ||
        (TIPOS_DELITO.includes(primero.tipo) ? primero.tipo : f.tipo_delito),
      ubicacion: f.ubicacion || primero.ubicacion || '',
      fecha_hecho:
        f.fecha_hecho || (primero.fecha_reporte ? String(primero.fecha_reporte).slice(0, 10) : ''),
      descripcion: f.descripcion || primero.descripcion || '',
      prioridad:
        f.prioridad === 'Media' && PRIORIDADES.includes(primero.prioridad)
          ? primero.prioridad
          : f.prioridad,
    }))
  }

  const checkDup = async () => {
    if (!form.case_number.trim() && form.titulo.trim().length < 4) {
      setSimilares([])
      return
    }
    try {
      const res = await expedientesApi.duplicados({
        case_number: form.case_number,
        titulo: form.titulo,
      })
      setSimilares(res.items || [])
    } catch {
      setSimilares([])
    }
  }

  const submit = async (e) => {
    e.preventDefault()
    if (incidentes.length === 0) {
      toast.error('Incidente requerido', 'Vincule al menos un incidente de origen.')
      return
    }
    if (!form.case_number.trim() || !form.titulo.trim() || !form.tipo_delito.trim()) {
      toast.error('Datos incompletos', 'Número de caso, título y tipo de delito son obligatorios.')
      return
    }
    if (form.fecha_hecho && form.fecha_hecho > hoyISO()) {
      toast.error('Fecha inválida', 'La fecha del hecho no puede ser futura.')
      return
    }
    setSaving(true)
    try {
      const row = await expedientesApi.registrar({
        ...form,
        incidente_ids: incidentes.map((i) => i.id_incidente),
      })
      toast.success('Expediente registrado', `${row.case_number} · estado ACTIVO`)
      onSaved()
    } catch (err) {
      toast.error('No se pudo registrar', err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <ModalShell title="Registrar nuevo expediente" onClose={onClose} icon={Plus}>
      <form onSubmit={submit} className="space-y-3">
        <IncidentesPicker selected={incidentes} onChange={onIncidentesChange} />

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm font-medium text-slate-700">
            Número de caso *
            <Input
              {...field(form, setForm, 'case_number')}
              onBlur={checkDup}
              className="mt-1.5"
              placeholder="Ej. HX-2026-0001"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Tipo de delito *
            <Select value={form.tipo_delito} onChange={onTipoChange} className="mt-1.5">
              <option value="">Seleccione…</option>
              {TIPOS_DELITO.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </Select>
          </label>
        </div>

        <IucrFields form={form} setForm={setForm} />

        <label className="block text-sm font-medium text-slate-700">
          Título *
          <Input
            {...field(form, setForm, 'titulo')}
            onBlur={checkDup}
            className="mt-1.5"
            placeholder="Resumen breve del caso"
          />
        </label>

        {similares.length > 0 && (
          <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50/80 p-3 text-sm text-amber-800">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p className="font-semibold">Posibles expedientes similares:</p>
              <ul className="mt-1 list-disc pl-4">
                {similares.map((s) => (
                  <li key={s.case_number}>
                    <span className="font-mono">{s.case_number}</span> — {s.titulo} ({s.estado})
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm font-medium text-slate-700">
            Fecha del hecho
            <Input
              type="date"
              max={hoyISO()}
              {...field(form, setForm, 'fecha_hecho')}
              className="mt-1.5"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Prioridad
            <Select {...field(form, setForm, 'prioridad')} className="mt-1.5">
              {PRIORIDADES.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </Select>
          </label>
        </div>

        <HechoExtraFields form={form} setForm={setForm} distritos={distritos} />

        <label className="block text-sm font-medium text-slate-700">
          Descripción
          <textarea
            {...field(form, setForm, 'descripcion')}
            rows={3}
            className="input-field mt-1.5"
            placeholder="Detalle del hecho…"
          />
        </label>

        <div className="flex justify-end gap-2 pt-1">
          <Button variant="secondary" type="button" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={saving}>
            <Plus className="h-4 w-4" />
            {saving ? 'Registrando…' : 'Registrar'}
          </Button>
        </div>
      </form>
    </ModalShell>
  )
}

function EditModal({ exp, onClose, onSaved, distritos = [] }) {
  const toast = useToast()
  const [form, setForm] = useState({
    titulo: exp.titulo || '',
    tipo_delito: exp.tipo_delito || '',
    fecha_hecho: exp.fecha_hecho || '',
    ubicacion: exp.ubicacion || '',
    prioridad: exp.prioridad || 'Media',
    descripcion: exp.descripcion || '',
    distrito: exp.distrito || '',
    sector: exp.sector || '',
    zona: exp.zona || '',
    cuadra: exp.cuadra || '',
    lugar_hecho: exp.lugar_hecho || '',
    iucr: exp.iucr || '',
    fbi_code: exp.fbi_code || '',
    arresto: exp.arresto || 'No',
    violencia_domestica: exp.violencia_domestica || 'No',
  })
  const [saving, setSaving] = useState(false)
  const [incidentes, setIncidentes] = useState([])
  const { onTipoChange } = useHechoHandlers(form, setForm)

  useEffect(() => {
    expedientesApi
      .incidentesVinculados(exp.case_number)
      .then((res) => setIncidentes(res.items || []))
      .catch(() => setIncidentes([]))
  }, [exp.case_number])

  const submit = async (e) => {
    e.preventDefault()
    if (form.fecha_hecho && form.fecha_hecho > hoyISO()) {
      toast.error('Fecha inválida', 'La fecha del hecho no puede ser futura.')
      return
    }
    if (incidentes.length === 0) {
      toast.error('Incidente requerido', 'El expediente debe conservar al menos un incidente.')
      return
    }
    setSaving(true)
    try {
      await expedientesApi.actualizar(exp.case_number, {
        ...form,
        incidente_ids: incidentes.map((i) => i.id_incidente),
      })
      toast.success('Expediente actualizado', exp.case_number)
      onSaved()
    } catch (err) {
      toast.error('No se pudo editar', err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <ModalShell title={`Editar expediente ${exp.case_number}`} onClose={onClose} icon={Pencil}>
      <form onSubmit={submit} className="space-y-3">
        <IncidentesPicker
          selected={incidentes}
          onChange={setIncidentes}
          excluirCase={exp.case_number}
        />

        <label className="block text-sm font-medium text-slate-700">
          Título
          <Input {...field(form, setForm, 'titulo')} className="mt-1.5" />
        </label>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm font-medium text-slate-700">
            Tipo de delito
            <Select value={form.tipo_delito} onChange={onTipoChange} className="mt-1.5">
              <option value="">Seleccione…</option>
              {TIPOS_DELITO.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </Select>
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Prioridad
            <Select {...field(form, setForm, 'prioridad')} className="mt-1.5">
              {PRIORIDADES.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </Select>
          </label>
        </div>

        <IucrFields form={form} setForm={setForm} />

        <label className="block text-sm font-medium text-slate-700">
          Fecha del hecho
          <Input type="date" max={hoyISO()} {...field(form, setForm, 'fecha_hecho')} className="mt-1.5" />
        </label>

        <HechoExtraFields form={form} setForm={setForm} distritos={distritos} />

        <label className="block text-sm font-medium text-slate-700">
          Descripción
          <textarea
            {...field(form, setForm, 'descripcion')}
            rows={3}
            className="input-field mt-1.5"
          />
        </label>
        <div className="flex justify-end gap-2 pt-1">
          <Button variant="secondary" type="button" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={saving}>
            {saving ? 'Guardando…' : 'Guardar cambios'}
          </Button>
        </div>
      </form>
    </ModalShell>
  )
}

const ACCION_META = {
  cerrar: { title: 'Cerrar expediente', icon: Lock, verb: 'Cerrar', danger: false },
  reabrir: { title: 'Reabrir expediente', icon: RotateCcw, verb: 'Reabrir', danger: false },
  archivar: { title: 'Archivar expediente', icon: Archive, verb: 'Archivar', danger: false },
  eliminar: { title: 'Eliminar expediente', icon: Trash2, verb: 'Eliminar', danger: true },
}

function EstadoModal({ exp, accion, onClose, onSaved }) {
  const toast = useToast()
  const [motivo, setMotivo] = useState('')
  const [saving, setSaving] = useState(false)
  const meta = ACCION_META[accion]

  const submit = async (e) => {
    e.preventDefault()
    if (!motivo.trim()) {
      toast.error('Motivo requerido', 'Indique el motivo de esta acción.')
      return
    }
    setSaving(true)
    try {
      if (accion === 'cerrar') await expedientesApi.cerrar(exp.case_number, motivo)
      else if (accion === 'reabrir') await expedientesApi.reabrir(exp.case_number, motivo)
      else if (accion === 'archivar') await expedientesApi.archivar(exp.case_number, motivo)
      else if (accion === 'eliminar') await expedientesApi.eliminar(exp.case_number, motivo)
      toast.success(`${meta.verb} expediente`, exp.case_number)
      onSaved()
    } catch (err) {
      toast.error('Acción no completada', err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <ModalShell title={`${meta.title} · ${exp.case_number}`} onClose={onClose} icon={meta.icon}>
      <form onSubmit={submit} className="space-y-3">
        {accion === 'eliminar' && (
          <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50/80 p-3 text-sm text-rose-800">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <p>
              La eliminación es <strong>lógica</strong>: el expediente queda en estado
              ELIMINADO con registro completo en auditoría. No se borra físicamente.
            </p>
          </div>
        )}
        <label className="block text-sm font-medium text-slate-700">
          Motivo *
          <textarea
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            rows={3}
            className="input-field mt-1.5"
            placeholder="Justifique la acción…"
            autoFocus
          />
        </label>
        <div className="flex justify-end gap-2 pt-1">
          <Button variant="secondary" type="button" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" variant={meta.danger ? 'danger' : 'primary'} disabled={saving}>
            <meta.icon className="h-4 w-4" />
            {saving ? 'Procesando…' : meta.verb}
          </Button>
        </div>
      </form>
    </ModalShell>
  )
}
