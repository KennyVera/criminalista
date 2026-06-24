import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ShieldCheck,
  RefreshCw,
  Download,
  Search,
  X,
  Eye,
  Activity,
  ShieldAlert,
  Users,
  AlertTriangle,
  Lock,
  CheckCircle2,
  FileClock,
} from 'lucide-react'
import { auditoriaApi } from '../api/auditoria'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Select, Spinner } from '../components/ui'
import { cn } from '../lib/cn'
import PageHeader from '../components/layout/PageHeader'
import StatCard from '../components/layout/StatCard'
import UserCell from '../components/layout/UserCell'
import TablePagination from '../components/layout/TablePagination'
import InfoPanel from '../components/layout/InfoPanel'

const SEVERIDAD_TONE = { critico: 'danger', alto: 'warning', medio: 'info', info: 'neutral' }
const SEVERIDAD_LABEL = { critico: 'Crítico', alto: 'Alto', medio: 'Medio', info: 'Informativo' }
const RESULTADO_TONE = { fallo: 'danger', exito: 'green', info: 'neutral' }
const RESULTADO_LABEL = { fallo: 'Fallido', exito: 'Exitoso', info: 'Informativo' }

const EMPTY_FILTERS = {
  q: '',
  accion: '',
  categoria: '',
  operacion: '',
  severidad: '',
  resultado: '',
  rol: '',
  ip: '',
  desde: '',
  hasta: '',
}

const OPERACION_OPTIONS = [
  { value: 'creacion', label: 'Creación' },
  { value: 'modificacion', label: 'Modificación' },
  { value: 'eliminacion', label: 'Eliminación' },
  { value: 'consulta', label: 'Consulta / Exportación' },
  { value: 'seguridad', label: 'Seguridad / Sesión' },
]

const OPERACION_LABEL = Object.fromEntries(OPERACION_OPTIONS.map((o) => [o.value, o.label]))
const OPERACION_TONE = {
  creacion: 'green',
  modificacion: 'info',
  eliminacion: 'danger',
  consulta: 'neutral',
  seguridad: 'warning',
}

function formatDate(value) {
  if (!value) return '—'
  try {
    return new Date(value).toLocaleString('es-CO')
  } catch {
    return String(value)
  }
}

export default function AuditoriaPage() {
  const { user } = useAuth()
  const toast = useToast()
  const isAdmin = user?.nombre_rol?.toLowerCase() === 'admin'

  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [qInput, setQInput] = useState('')
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(15)
  const [data, setData] = useState({
    items: [],
    total: 0,
    total_pages: 1,
    stats: {},
    acciones: [],
    categorias: [],
    roles: [],
  })
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)
  const [verifying, setVerifying] = useState(false)
  const [integrity, setIntegrity] = useState(null)
  const [selected, setSelected] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await auditoriaApi.eventos({ ...filters, page, per_page: perPage })
      setData(res)
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setLoading(false)
    }
  }, [filters, page, perPage, toast])

  useEffect(() => {
    if (isAdmin) load()
  }, [isAdmin, load])

  // Debounce de la búsqueda de texto.
  useEffect(() => {
    const t = setTimeout(() => {
      setFilters((f) => (f.q === qInput ? f : { ...f, q: qInput }))
      setPage(1)
    }, 350)
    return () => clearTimeout(t)
  }, [qInput])

  const setFilter = (key, value) => {
    setFilters((f) => ({ ...f, [key]: value }))
    setPage(1)
  }

  const resetFilters = () => {
    setFilters(EMPTY_FILTERS)
    setQInput('')
    setPage(1)
  }

  const handleExport = async () => {
    setExporting(true)
    try {
      await auditoriaApi.exportarCsv(filters)
      toast.success('Exportación', 'Archivo CSV generado. La exportación quedó auditada.')
      load()
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setExporting(false)
    }
  }

  const handleVerify = async () => {
    setVerifying(true)
    try {
      const [cadena, custodia] = await Promise.all([
        auditoriaApi.verificarIntegridad(),
        auditoriaApi.verificarCustodia(),
      ])
      const ok = cadena.ok && custodia.ok
      setIntegrity({ cadena, custodia, ok })
      if (ok) {
        toast.success('Integridad verificada', 'La cadena de auditoría y la custodia son íntegras.')
      } else {
        toast.error('Alerta de integridad', 'Se detectaron observaciones. Revise el detalle.')
      }
      load()
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setVerifying(false)
    }
  }

  const activeFilters = useMemo(
    () => Object.entries(filters).filter(([, v]) => v !== '').length,
    [filters]
  )

  const stats = data.stats || {}
  const moduleTabs = ['Todos', ...(data.categorias || [])]
  const activeModule = filters.categoria || 'Todos'
  const selectModule = (m) => setFilter('categoria', m === 'Todos' ? '' : m)

  if (!isAdmin) {
    return (
      <Card className="border-amber-200/80">
        <p className="font-semibold text-amber-900 dark:text-amber-200">Acceso restringido</p>
        <p className="mt-1 text-sm text-amber-800 dark:text-amber-300">
          Solo los roles de Auditoría / Administración pueden consultar la auditoría del sistema.
        </p>
      </Card>
    )
  }

  return (
    <section className="space-y-6 animate-fade-up">
      <PageHeader
        title="Auditoría y trazabilidad"
        subtitle="Paquete Auditoría (P03) — eventos inmutables del sistema"
        dataset="app_audit_logs"
        icon={ShieldCheck}
        actions={
          <>
            <Button type="button" variant="secondary" onClick={load} disabled={loading}>
              <RefreshCw className={loading ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} />
              Actualizar
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={handleVerify}
              disabled={verifying}
            >
              <ShieldCheck className={verifying ? 'h-4 w-4 animate-pulse' : 'h-4 w-4'} />
              Verificar integridad
            </Button>
            <Button
              type="button"
              variant="primary"
              onClick={handleExport}
              disabled={exporting || data.total === 0}
            >
              <Download className={exporting ? 'h-4 w-4 animate-pulse' : 'h-4 w-4'} />
              Exportar CSV
            </Button>
          </>
        }
      />

      {integrity && (
        <div
          className={cn(
            'rounded-2xl border px-5 py-4',
            integrity.ok
              ? 'border-emerald-200 bg-emerald-50/70'
              : 'border-rose-200 bg-rose-50/70'
          )}
        >
          <div className="flex items-start gap-3">
            {integrity.ok ? (
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
            ) : (
              <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-rose-600" />
            )}
            <div className="flex-1">
              <p className={cn('font-semibold', integrity.ok ? 'text-emerald-800' : 'text-rose-800')}>
                {integrity.ok
                  ? 'Integridad verificada (CU-O75 / CU-O15)'
                  : 'Se detectaron alertas de integridad'}
              </p>
              <ul className="mt-1 space-y-0.5 text-sm text-slate-700">
                <li>
                  <span className="font-medium">Cadena de auditoría:</span> {integrity.cadena.mensaje}{' '}
                  ({integrity.cadena.verificados} verificados
                  {integrity.cadena.sin_sello ? `, ${integrity.cadena.sin_sello} sin sello` : ''})
                </li>
                <li>
                  <span className="font-medium">Cadena de custodia:</span> {integrity.custodia.mensaje}{' '}
                  ({integrity.custodia.verificadas} verificadas)
                </li>
              </ul>
              {!integrity.ok && (
                <div className="mt-2 space-y-1 text-xs text-rose-700">
                  {(integrity.cadena.rupturas || []).slice(0, 5).map((r) => (
                    <p key={`c-${r.id_log}`}>
                      · Evento #{r.id_log} ({r.accion}): {r.problemas.join('; ')}
                    </p>
                  ))}
                  {(integrity.custodia.alertas || []).slice(0, 5).map((a, i) => (
                    <p key={`e-${a.id_evidencia}-${i}`}>
                      · Evidencia #{a.id_evidencia} (caso {a.caso}): {a.motivo}
                    </p>
                  ))}
                </div>
              )}
            </div>
            <button
              type="button"
              onClick={() => setIntegrity(null)}
              className="rounded-lg p-1 text-slate-400 transition hover:bg-white/60 hover:text-slate-600"
              aria-label="Cerrar"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Eventos (según filtros)"
          value={(stats.total ?? 0).toLocaleString('es-CO')}
          sub="Registros de auditoría"
          sparkline="blue"
          icon={Activity}
        />
        <StatCard
          label="Fallos de seguridad"
          value={(stats.fallos_seguridad ?? 0).toLocaleString('es-CO')}
          sub="Login fallido, accesos denegados…"
          sparkline="purple"
          icon={ShieldAlert}
        />
        <StatCard
          label="Eventos críticos / altos"
          value={(stats.eventos_criticos ?? 0).toLocaleString('es-CO')}
          sub="Requieren revisión"
          sparkline="green"
          icon={AlertTriangle}
        />
        <StatCard
          label="Usuarios distintos"
          value={(stats.usuarios_distintos ?? 0).toLocaleString('es-CO')}
          sub={`${stats.ips_distintas ?? 0} IP(s) registradas`}
          sparkline="blue"
          icon={Users}
        />
      </div>

      {/* Filtros avanzados */}
      <Card className="space-y-4">
        {/* Tabs de módulo (reemplazan el combobox de categorías) */}
        <div
          role="tablist"
          aria-label="Filtrar por módulo"
          className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1"
        >
          {moduleTabs.map((m) => {
            const active = activeModule === m
            return (
              <button
                key={m}
                type="button"
                role="tab"
                aria-selected={active}
                onClick={() => selectModule(m)}
                className={cn(
                  'shrink-0 whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-semibold transition-all duration-200',
                  active
                    ? 'bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white shadow-md shadow-indigo-500/25'
                    : 'border border-slate-200/70 bg-white/70 text-slate-600 backdrop-blur-sm hover:bg-white hover:text-[#0F172A]'
                )}
              >
                {m}
              </button>
            )
          })}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="relative w-full max-w-md">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              value={qInput}
              onChange={(e) => setQInput(e.target.value)}
              placeholder="Buscar por usuario, acción, IP, detalle…"
              className="input-field pl-10"
            />
          </div>
          {activeFilters > 0 && (
            <Button type="button" variant="ghost" size="sm" onClick={resetFilters}>
              <X className="h-4 w-4" />
              Limpiar filtros ({activeFilters})
            </Button>
          )}
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-7">
          <Select
            value={filters.rol}
            onChange={(e) => setFilter('rol', e.target.value)}
            aria-label="Filtrar por tipo de actor"
          >
            <option value="">Todo actor (rol)</option>
            {(data.roles || []).map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </Select>
          <Select
            value={filters.accion}
            onChange={(e) => setFilter('accion', e.target.value)}
            aria-label="Filtrar por acción"
          >
            <option value="">Todas las acciones</option>
            {(data.acciones || []).map((a) => (
              <option key={a.value} value={a.value}>
                {a.label}
              </option>
            ))}
          </Select>
          <Select
            value={filters.operacion}
            onChange={(e) => setFilter('operacion', e.target.value)}
            aria-label="Filtrar por operación"
          >
            <option value="">Toda operación</option>
            {OPERACION_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </Select>
          <Select
            value={filters.severidad}
            onChange={(e) => setFilter('severidad', e.target.value)}
            aria-label="Filtrar por severidad"
          >
            <option value="">Toda severidad</option>
            <option value="critico">Crítico</option>
            <option value="alto">Alto</option>
            <option value="medio">Medio</option>
            <option value="info">Informativo</option>
          </Select>
          <Select
            value={filters.resultado}
            onChange={(e) => setFilter('resultado', e.target.value)}
            aria-label="Filtrar por resultado"
          >
            <option value="">Todo resultado</option>
            <option value="exito">Exitoso</option>
            <option value="fallo">Fallido</option>
            <option value="info">Informativo</option>
          </Select>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Desde
            </span>
            <input
              type="date"
              value={filters.desde}
              onChange={(e) => setFilter('desde', e.target.value)}
              className="input-field"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Hasta
            </span>
            <input
              type="date"
              value={filters.hasta}
              onChange={(e) => setFilter('hasta', e.target.value)}
              className="input-field"
            />
          </label>
        </div>
      </Card>

      {/* Tabla de eventos */}
      <Card flush className="overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-20">
            <Spinner />
          </div>
        ) : data.items.length === 0 ? (
          <p className="py-20 text-center body-text">
            No se encontraron eventos de auditoría con los filtros actuales.
          </p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="data-table min-w-[1040px]">
                <thead>
                  <tr>
                    <th>Fecha y hora (UTC)</th>
                    <th>Usuario</th>
                    <th>Rol</th>
                    <th>Acción</th>
                    <th>Módulo</th>
                    <th>Severidad</th>
                    <th>Resultado</th>
                    <th>IP</th>
                    <th className="text-center">Detalle</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((row) => (
                    <tr key={row.id_log ?? `${row.fecha_hora}-${row.accion}`}>
                      <td className="caption-text whitespace-nowrap">{formatDate(row.fecha_hora)}</td>
                      <td>
                        <UserCell name={row.usuario} email={row.email || '—'} />
                      </td>
                      <td>
                        {row.rol ? <Badge tone="info">{row.rol}</Badge> : <span className="caption-text">—</span>}
                      </td>
                      <td>
                        <span className="font-semibold text-black">{row.accion_label}</span>
                        <span className="block font-mono text-[11px] text-slate-500">{row.accion}</span>
                      </td>
                      <td className="caption-text">{row.categoria}</td>
                      <td>
                        <Badge tone={SEVERIDAD_TONE[row.severidad] || 'neutral'}>
                          {SEVERIDAD_LABEL[row.severidad] || row.severidad}
                        </Badge>
                      </td>
                      <td>
                        <Badge tone={RESULTADO_TONE[row.resultado] || 'neutral'}>
                          {RESULTADO_LABEL[row.resultado] || row.resultado}
                        </Badge>
                      </td>
                      <td className="font-mono caption-text">{row.direccion_ip || '—'}</td>
                      <td className="text-center">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelected(row)}
                          aria-label="Ver detalle del evento"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <TablePagination
              page={page}
              totalPages={data.total_pages}
              totalItems={data.total}
              perPage={perPage}
              onPageChange={setPage}
              onPerPageChange={(n) => {
                setPerPage(n)
                setPage(1)
              }}
              itemLabel={data.total === 1 ? 'evento' : 'eventos'}
            />
          </>
        )}
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <InfoPanel title="Registro inmutable" icon={Lock}>
          <p className="flex items-center gap-1.5 text-emerald-700 dark:text-emerald-400">
            <CheckCircle2 className="h-4 w-4" />
            Eventos append-only
          </p>
          <p className="mt-1 text-xs">
            Cada operación sensible queda registrada con usuario, rol, IP y marca de tiempo en UTC.
          </p>
        </InfoPanel>
        <InfoPanel title="Trazabilidad total" icon={FileClock}>
          <p className="text-xs">
            Autenticación y sesiones, CRUD de usuarios, cambios de permisos, políticas y
            configuración, respaldos y exportaciones quedan auditados.
          </p>
        </InfoPanel>
        <InfoPanel title="Exportación auditada" icon={Download}>
          <p className="text-xs">
            La exportación de la auditoría genera a su vez un evento (CU-O74), preservando la cadena
            de trazabilidad y el cumplimiento.
          </p>
        </InfoPanel>
      </div>

      {selected && <EventDetailModal event={selected} onClose={() => setSelected(null)} />}
    </section>
  )
}

function DetailRow({ label, children, mono = false }) {
  return (
    <div className="grid grid-cols-3 gap-3 border-b border-slate-100 py-2.5 last:border-0 dark:border-slate-800">
      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className={`col-span-2 text-sm font-medium text-black ${mono ? 'font-mono break-all' : ''}`}>
        {children}
      </dd>
    </div>
  )
}

function EventDetailModal({ event, onClose }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="ct-card max-h-[85vh] w-full max-w-2xl overflow-y-auto p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="page-icon">
              <ShieldCheck className="h-6 w-6" strokeWidth={1.75} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-black">{event.accion_label}</h2>
              <p className="font-mono text-xs text-slate-500">
                {event.accion} · evento #{event.id_log ?? '—'}
              </p>
            </div>
          </div>
          <Button type="button" variant="ghost" size="sm" onClick={onClose} aria-label="Cerrar">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="mb-4 flex flex-wrap gap-2">
          <Badge tone={SEVERIDAD_TONE[event.severidad] || 'neutral'}>
            Severidad: {SEVERIDAD_LABEL[event.severidad] || event.severidad}
          </Badge>
          <Badge tone={RESULTADO_TONE[event.resultado] || 'neutral'}>
            {RESULTADO_LABEL[event.resultado] || event.resultado}
          </Badge>
          <Badge tone="info">{event.categoria}</Badge>
          {event.operacion && (
            <Badge tone={OPERACION_TONE[event.operacion] || 'neutral'}>
              {OPERACION_LABEL[event.operacion] || event.operacion}
            </Badge>
          )}
        </div>

        <dl>
          <DetailRow label="Fecha y hora (UTC)">{formatDate(event.fecha_hora)}</DetailRow>
          <DetailRow label="Usuario">
            {event.usuario}
            {event.email ? <span className="text-slate-500"> · {event.email}</span> : null}
          </DetailRow>
          <DetailRow label="Rol">{event.rol || '—'}</DetailRow>
          <DetailRow label="Placa">{event.placa || '—'}</DetailRow>
          <DetailRow label="Tabla afectada" mono>
            {event.tabla_afectada || '—'}
          </DetailRow>
          <DetailRow label="Dirección IP" mono>
            {event.direccion_ip || '—'}
          </DetailRow>
          <DetailRow label="Detalle">{event.detalle || '—'}</DetailRow>
        </dl>

        {(event.datos_anteriores || event.datos_nuevos) && (
          <div
            className={cn(
              'mt-5 grid gap-3',
              event.datos_anteriores && event.datos_nuevos ? 'md:grid-cols-2' : 'grid-cols-1'
            )}
          >
            {event.datos_anteriores && (
              <DataPanel title="Datos anteriores" accent="amber" value={event.datos_anteriores} />
            )}
            {event.datos_nuevos && (
              <DataPanel title="Datos nuevos" accent="emerald" value={event.datos_nuevos} />
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function DataPanel({ title, accent, value }) {
  const accents = {
    amber: 'border-l-amber-400',
    emerald: 'border-l-emerald-400',
  }
  let parsed = null
  try {
    parsed = JSON.parse(value)
  } catch {
    parsed = null
  }
  const isObject = parsed && typeof parsed === 'object' && !Array.isArray(parsed)

  return (
    <div
      className={cn(
        'rounded-2xl border border-l-4 border-slate-200/70 bg-slate-50/70 p-4',
        accents[accent] || 'border-l-slate-300'
      )}
    >
      <p className="mb-2.5 text-xs font-bold uppercase tracking-wide text-slate-500">{title}</p>
      {isObject ? (
        <dl className="space-y-1.5">
          {Object.entries(parsed).map(([k, v]) => (
            <div key={k} className="grid grid-cols-5 gap-2 text-xs">
              <dt className="col-span-2 truncate font-semibold text-slate-600" title={k}>
                {k}
              </dt>
              <dd className="col-span-3 break-all font-medium text-black">
                {v === null || v === '' ? '—' : String(v)}
              </dd>
            </div>
          ))}
        </dl>
      ) : (
        <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-words font-mono text-xs text-black">
          {value}
        </pre>
      )}
    </div>
  )
}
