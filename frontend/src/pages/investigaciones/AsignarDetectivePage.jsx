import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  UserPlus,
  RefreshCw,
  UserMinus,
  ArrowRightLeft,
  Search,
  FileText,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { asignacionesApi } from '../../api/asignaciones'
import { expedientesApi } from '../../api/expedientes'
import { Button, Card, Badge, Spinner } from '../../components/ui'
import { useToast } from '../../context/ToastContext'
import { canManageAsignaciones, isAdmin } from '../../utils/roles'
import { Navigate } from 'react-router-dom'

const ESTADOS = ['', 'Abierto', 'En investigación', 'Importado', 'Cerrado', 'Archivado']
const PRIORIDADES = ['', 'Baja', 'Media', 'Alta', 'Crítica']
const FILTROS_ASIGNACION = [
  { value: 'sin_asignar', label: 'Sin asignar' },
  { value: 'asignados', label: 'Asignados' },
  { value: 'todos', label: 'Todos los casos' },
]

export default function AsignarDetectivePage() {
  const { user } = useAuth()
  const toast = useToast()
  const [detectives, setDetectives] = useState([])
  const [casos, setCasos] = useState([])
  const [casosMeta, setCasosMeta] = useState({ totalItems: 0, totalPages: 1, page: 1, message: '' })
  const [loadingDet, setLoadingDet] = useState(true)
  const [loadingCasos, setLoadingCasos] = useState(false)
  const [searchQ, setSearchQ] = useState('')
  const [filtroEstado, setFiltroEstado] = useState('')
  const [filtroPrioridad, setFiltroPrioridad] = useState('')
  const [page, setPage] = useState(1)
  const [fkCaso, setFkCaso] = useState('')
  const [fkDetective, setFkDetective] = useState('')
  const [observaciones, setObservaciones] = useState('')
  const [filtroAsignacion, setFiltroAsignacion] = useState('sin_asignar')
  const [busy, setBusy] = useState(false)
  const [pdfBusy, setPdfBusy] = useState(null)

  const allowed = canManageAsignaciones(user) || isAdmin(user)

  const loadDetectives = useCallback(async () => {
    setLoadingDet(true)
    try {
      const d = await asignacionesApi.detectivesDisponibles()
      setDetectives(d.items || [])
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setLoadingDet(false)
    }
  }, [toast])

  const loadCasos = useCallback(async () => {
    setLoadingCasos(true)
    try {
      const res = await asignacionesApi.casos({
        q: searchQ.trim(),
        page,
        perPage: 20,
        soloSinAsignar: filtroAsignacion === 'sin_asignar',
        soloAsignados: filtroAsignacion === 'asignados',
        estado: filtroEstado,
        prioridad: filtroPrioridad,
      })
      setCasos(res.items || [])
      setCasosMeta({
        totalItems: res.totalItems ?? 0,
        totalPages: res.totalPages ?? 1,
        page: res.page ?? page,
        message: res.message || '',
      })
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setLoadingCasos(false)
    }
  }, [searchQ, page, filtroAsignacion, filtroEstado, filtroPrioridad, toast])

  useEffect(() => {
    if (allowed) loadDetectives()
  }, [allowed, loadDetectives])

  useEffect(() => {
    if (!allowed) return
    const t = setTimeout(() => loadCasos(), searchQ.trim() ? 400 : 0)
    return () => clearTimeout(t)
  }, [allowed, loadCasos, searchQ, page, filtroAsignacion, filtroEstado, filtroPrioridad])

  const selectedCaso = casos.find((c) => String(c.id) === String(fkCaso))

  const selectCaso = (c) => {
    setFkCaso(String(c.id))
  }

  const handleAsignar = async (e) => {
    e.preventDefault()
    if (!fkCaso || !fkDetective) {
      toast.error('Datos incompletos', 'Seleccione caso y detective')
      return
    }
    setBusy(true)
    try {
      if (selectedCaso?.asignacion_activa) {
        await asignacionesApi.reasignar(Number(fkCaso), {
          fk_detective: Number(fkDetective),
          observaciones,
        })
        toast.success('Reasignado', 'Detective actualizado y notificado')
      } else {
        await asignacionesApi.asignar({
          fk_caso: Number(fkCaso),
          fk_detective: Number(fkDetective),
          observaciones,
        })
        toast.success('Asignado', 'Caso asignado; se registró fecha y notificación')
      }
      setObservaciones('')
      loadDetectives()
      loadCasos()
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setBusy(false)
    }
  }

  const handleRemover = async () => {
    if (!fkCaso) return
    if (!window.confirm('¿Remover al detective de este caso?')) return
    setBusy(true)
    try {
      await asignacionesApi.remover(Number(fkCaso), { motivo: 'Removido desde panel Comisario' })
      toast.success('Removido', 'El caso quedó sin detective asignado')
      loadDetectives()
      loadCasos()
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setBusy(false)
    }
  }

  const handlePdf = async (caseNumber, e) => {
    e?.stopPropagation()
    setPdfBusy(caseNumber)
    try {
      await expedientesApi.downloadInformePdf(caseNumber)
      toast.success('PDF generado', 'Informe penal descargado')
    } catch (err) {
      toast.error('PDF', err.message)
    } finally {
      setPdfBusy(null)
    }
  }

  if (!allowed) return <Navigate to="/" replace />

  return (
    <section className="mx-auto max-w-7xl space-y-6">
      <header>
        <h2 className="text-xl font-bold text-slate-900">Asignar detective a caso</h2>
        <p className="mt-1 text-sm text-slate-500">
          Explore el catálogo de casos sin memorizar el número, filtre por estado o prioridad y
          genere informes PDF con estructura profesional (Ecuador).
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-semibold text-slate-900">Detectives y carga laboral</h3>
            <Button
              type="button"
              variant="secondary"
              className="!px-2 !py-1"
              onClick={loadDetectives}
              disabled={loadingDet}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
          {loadingDet ? (
            <div className="flex justify-center py-12">
              <Spinner />
            </div>
          ) : (
            <ul className="max-h-80 space-y-2 overflow-y-auto">
              {detectives.map((d) => (
                <li
                  key={d.id_usuario}
                  className={`rounded-xl border px-3 py-2 text-sm ${
                    String(fkDetective) === String(d.id_usuario)
                      ? 'border-brand-500 bg-brand-50'
                      : 'border-slate-100'
                  }`}
                >
                  <button
                    type="button"
                    className="w-full text-left"
                    onClick={() => setFkDetective(String(d.id_usuario))}
                  >
                    <p className="font-medium text-slate-900">{d.etiqueta}</p>
                    <p className="text-xs text-slate-500">{d.email}</p>
                    <div className="mt-1 flex items-center gap-2">
                      <Badge tone={d.disponible ? 'green' : 'red'}>
                        {d.casos_activos} casos activos
                      </Badge>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className="p-4">
          <form onSubmit={handleAsignar} className="space-y-4">
            <label className="block text-sm font-medium text-slate-700">
              Buscar caso (opcional)
              <div className="relative mt-1">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="search"
                  value={searchQ}
                  onChange={(e) => {
                    setSearchQ(e.target.value)
                    setPage(1)
                  }}
                  placeholder="Número, tipo de delito, distrito…"
                  className="w-full rounded-xl border border-slate-200 py-2 pl-9 pr-3 text-sm"
                />
              </div>
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="block text-sm font-medium text-slate-700">
                Estado
                <select
                  value={filtroEstado}
                  onChange={(e) => {
                    setFiltroEstado(e.target.value)
                    setPage(1)
                  }}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                >
                  {ESTADOS.map((e) => (
                    <option key={e || 'all'} value={e}>
                      {e || 'Todos'}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Prioridad
                <select
                  value={filtroPrioridad}
                  onChange={(e) => {
                    setFiltroPrioridad(e.target.value)
                    setPage(1)
                  }}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                >
                  {PRIORIDADES.map((p) => (
                    <option key={p || 'all'} value={p}>
                      {p || 'Todas'}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label className="block text-sm font-medium text-slate-700">
              Asignación
              <select
                value={filtroAsignacion}
                onChange={(e) => {
                  setFiltroAsignacion(e.target.value)
                  setPage(1)
                }}
                className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
              >
                {FILTROS_ASIGNACION.map((f) => (
                  <option key={f.value} value={f.value}>
                    {f.label}
                  </option>
                ))}
              </select>
            </label>

            {selectedCaso && (
              <p className="rounded-lg bg-brand-50 px-3 py-2 text-xs text-brand-900">
                Caso seleccionado: <strong>{selectedCaso.case_number}</strong>
                {selectedCaso.primary_type ? ` — ${selectedCaso.primary_type}` : ''}
              </p>
            )}

            {selectedCaso?.asignacion_activa && (
              <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">
                Este caso ya tiene detective. Al guardar se <strong>reasignará</strong>.
              </p>
            )}

            <label className="block text-sm font-medium text-slate-700">
              Observaciones
              <textarea
                value={observaciones}
                onChange={(e) => setObservaciones(e.target.value)}
                rows={2}
                className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
              />
            </label>

            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={busy || !fkCaso || !fkDetective}>
                {selectedCaso?.asignacion_activa ? (
                  <>
                    <ArrowRightLeft className="h-4 w-4" />
                    Reasignar
                  </>
                ) : (
                  <>
                    <UserPlus className="h-4 w-4" />
                    Asignar
                  </>
                )}
              </Button>
              {selectedCaso?.asignacion_activa && (
                <Button type="button" variant="secondary" disabled={busy} onClick={handleRemover}>
                  <UserMinus className="h-4 w-4" />
                  Remover
                </Button>
              )}
            </div>
          </form>
        </Card>
      </div>

      <Card className="overflow-hidden p-0">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-4 py-3">
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <h3 className="font-semibold text-slate-900">Catálogo de casos</h3>
              <p className="text-xs text-slate-500">{casosMeta.message}</p>
            </div>
            <label className="text-xs font-medium text-slate-600">
              Mostrar
              <select
                value={filtroAsignacion}
                onChange={(e) => {
                  setFiltroAsignacion(e.target.value)
                  setPage(1)
                }}
                className="ml-2 rounded-lg border border-slate-200 px-2 py-1.5 text-sm text-slate-800"
              >
                {FILTROS_ASIGNACION.map((f) => (
                  <option key={f.value} value={f.value}>
                    {f.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <Button type="button" variant="secondary" className="!py-1.5" onClick={loadCasos}>
            <RefreshCw className="h-4 w-4" />
            Actualizar
          </Button>
        </div>

        {loadingCasos ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">N.º caso</th>
                  <th className="px-4 py-3">Tipo delito</th>
                  <th className="px-4 py-3">Distrito</th>
                  <th className="px-4 py-3">Fecha hecho</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3">Prioridad</th>
                  <th className="px-4 py-3">Detective</th>
                  <th className="px-4 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {casos.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-10 text-center text-slate-500">
                      No hay casos con los filtros actuales.
                    </td>
                  </tr>
                ) : (
                  casos.map((c) => {
                    const selected = String(fkCaso) === String(c.id)
                    return (
                      <tr
                        key={c.id}
                        onClick={() => selectCaso(c)}
                        className={`cursor-pointer transition-colors hover:bg-slate-50 ${
                          selected ? 'bg-brand-50/70 ring-1 ring-inset ring-brand-200' : ''
                        }`}
                      >
                        <td className="px-4 py-3 font-medium text-slate-900">{c.case_number}</td>
                        <td className="max-w-[140px] truncate px-4 py-3 text-slate-600">
                          {c.primary_type || '—'}
                        </td>
                        <td className="px-4 py-3 text-slate-600">{c.district || '—'}</td>
                        <td className="whitespace-nowrap px-4 py-3 text-slate-600">
                          {c.fecha_hecho || c.fecha_reporte || '—'}
                        </td>
                        <td className="px-4 py-3">
                          <Badge tone="slate">{c.estado_caso || '—'}</Badge>
                        </td>
                        <td className="px-4 py-3">
                          <Badge
                            tone={
                              c.prioridad_caso === 'Crítica' || c.prioridad_caso === 'Alta'
                                ? 'red'
                                : 'slate'
                            }
                          >
                            {c.prioridad_caso || '—'}
                          </Badge>
                        </td>
                        <td className="max-w-[120px] truncate px-4 py-3 text-slate-600">
                          {c.detective_actual || 'Sin asignar'}
                        </td>
                        <td className="px-4 py-3">
                          <div
                            className="flex items-center justify-end gap-1"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Button
                              type="button"
                              variant="secondary"
                              className="!px-2 !py-1"
                              title="Informe PDF Ecuador"
                              disabled={pdfBusy === c.case_number}
                              onClick={(e) => handlePdf(c.case_number, e)}
                            >
                              <FileText className="h-4 w-4" />
                            </Button>
                            <Link
                              to={`/expedientes/${encodeURIComponent(c.case_number)}`}
                              className="inline-flex rounded-lg border border-slate-200 p-1.5 text-slate-600 hover:bg-slate-50"
                              title="Abrir expediente"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </Link>
                          </div>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3">
          <p className="text-xs text-slate-500">
            Página {casosMeta.page} de {casosMeta.totalPages} · {casosMeta.totalItems?.toLocaleString()} casos
          </p>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="secondary"
              className="!px-2 !py-1"
              disabled={page <= 1 || loadingCasos}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="secondary"
              className="!px-2 !py-1"
              disabled={page >= casosMeta.totalPages || loadingCasos}
              onClick={() => setPage((p) => p + 1)}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </section>
  )
}
