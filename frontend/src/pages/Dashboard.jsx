import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
  ResponsiveContainer,
} from 'recharts'
import {
  Activity,
  BarChart3,
  Filter,
  Map,
  Shield,
  TrendingUp,
  Users,
  Database,
  Sparkles,
} from 'lucide-react'
import { dashboardApi } from '../api/dashboard'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { canAccessDataCrud, canViewDashboard, canViewInvestigacionProgress, canViewOperationalIndicators } from '../utils/roles'
import { Badge, Button, Card, Spinner } from '../components/ui'

function KpiCard({ label, value, sub, icon: Icon, accent = 'from-blue-600 to-indigo-600' }) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-white/60 bg-white/80 p-5 shadow-lg shadow-slate-200/40 backdrop-blur-md transition hover:-translate-y-0.5 hover:shadow-xl">
      <div
        className={`absolute -right-6 -top-6 h-28 w-28 rounded-full bg-gradient-to-br ${accent} opacity-20 blur-2xl transition group-hover:opacity-30`}
      />
      <div className="relative flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
            {typeof value === 'number' ? value.toLocaleString('es-CO') : value ?? '—'}
          </p>
          {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
        </div>
        <div className={`rounded-xl bg-gradient-to-br ${accent} p-3 text-white shadow-lg`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  )
}

const TABS = [
  { id: 'resumen', label: 'Resumen', icon: BarChart3 },
  { id: 'filtros', label: 'Filtros', icon: Filter },
  { id: 'mapa', label: 'Mapa de calor', icon: Map },
  { id: 'ranking', label: 'Ranking', icon: Users },
  { id: 'indicadores', label: 'Indicadores', icon: Activity, analistaOnly: true },
]

const EMPTY_FILTERS = { zona: '', tipo: '', anio: '', mes: '' }

function FilterSelect({ label, value, onChange, children, disabled }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-600">{label}</span>
      <select
        value={value}
        onChange={onChange}
        disabled={disabled}
        className="w-full cursor-pointer rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100 disabled:opacity-60"
      >
        {children}
      </select>
    </label>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const toast = useToast()
  const showCrud = canAccessDataCrud(user)
  const showIndicadores = canViewOperationalIndicators(user)
  const canView = canViewDashboard(user)

  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('resumen')
  const [filterDraft, setFilterDraft] = useState(EMPTY_FILTERS)
  const [filterOptions, setFilterOptions] = useState({
    distritos: [],
    tipos_delito: [],
    anios: [],
    meses: [],
  })
  const [filtered, setFiltered] = useState(null)
  const [filtering, setFiltering] = useState(false)
  const [optionsLoading, setOptionsLoading] = useState(true)
  const [ranking, setRanking] = useState([])
  const [rankingLoading, setRankingLoading] = useState(false)

  const loadOverview = useCallback(async () => {
    if (!canView) return
    setLoading(true)
    try {
      const data = await dashboardApi.overview()
      setStats(data)
    } catch (e) {
      toast.error('Error', e.message || 'No se pudo cargar el dashboard')
    } finally {
      setLoading(false)
    }
  }, [toast, canView])

  useEffect(() => {
    if (canView) loadOverview()
  }, [loadOverview, canView])

  const loadRanking = useCallback(async () => {
    if (!canView) return
    setRankingLoading(true)
    try {
      const res = await dashboardApi.rankingDetectives()
      setRanking(res.items || [])
      if (res.tasa_resolucion) {
        setStats((prev) =>
          prev
            ? {
                ...prev,
                operational_indicators: {
                  ...(prev.operational_indicators || {}),
                  tasa_resolucion: res.tasa_resolucion,
                },
              }
            : prev
        )
      }
    } catch (e) {
      toast.error('Error', e.message || 'No se pudo actualizar el ranking')
    } finally {
      setRankingLoading(false)
    }
  }, [toast, canView])

  useEffect(() => {
    if (tab !== 'ranking' || !canView) return
    loadRanking()
    const timer = setInterval(loadRanking, 15000)
    return () => clearInterval(timer)
  }, [tab, canView, loadRanking])

  useEffect(() => {
    if (stats?.detective_ranking?.length) {
      setRanking(stats.detective_ranking)
    }
  }, [stats?.detective_ranking])

  const fetchFilteredStats = useCallback(async (params, { silent = false } = {}) => {
    setFiltering(true)
    try {
      const data = await dashboardApi.filtros(params)
      setFiltered(data)
      if (!silent) {
        toast.success('Éxito', 'Estadísticas actualizadas')
      }
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setFiltering(false)
    }
  }, [toast])

  useEffect(() => {
    if (!canView) return
    let cancelled = false
    ;(async () => {
      setOptionsLoading(true)
      try {
        const [opts] = await Promise.all([
          dashboardApi.filtrosOpciones(),
          fetchFilteredStats(EMPTY_FILTERS, { silent: true }),
        ])
        if (!cancelled) setFilterOptions(opts)
      } catch (e) {
        if (!cancelled) toast.error('Error', e.message || 'No se cargaron opciones de filtro')
      } finally {
        if (!cancelled) setOptionsLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [fetchFilteredStats, toast, canView])

  const applyFilters = async () => {
    await fetchFilteredStats(filterDraft)
    setTab('filtros')
  }

  const clearFilters = async () => {
    setFilterDraft(EMPTY_FILTERS)
    await fetchFilteredStats(EMPTY_FILTERS, { silent: true })
  }

  const hasActiveFilters = Boolean(
    filterDraft.zona || filterDraft.tipo || filterDraft.anio || filterDraft.mes
  )

  const tabs = useMemo(
    () => TABS.filter((t) => !t.analistaOnly || showIndicadores),
    [showIndicadores]
  )

  if (!canView) {
    if (canViewInvestigacionProgress(user)) {
      return <Navigate to="/investigaciones/progreso" replace />
    }
    return <Navigate to="/tabla/dim_caso" replace />
  }

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Spinner />
      </div>
    )
  }

  const t = stats?.totals || {}
  const chartDims = (stats?.dimension_counts || []).slice(0, 8)
  const byDistrict = stats?.crimes_by_district?.items || []
  const byType = stats?.crimes_by_type || []
  const heatMap = stats?.heat_map || []
  const operational = stats?.operational_indicators || {}
  const trend = operational?.tendencias_delictivas || []

  return (
    <section className="space-y-8">
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-900 px-6 py-8 text-white shadow-2xl md:px-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(59,130,246,0.35),_transparent_50%)]" />
        <div className="relative flex flex-wrap items-end justify-between gap-6">
          <div>
            <p className="flex items-center gap-2 text-sm text-blue-200">
              <Sparkles className="h-4 w-4" />
              Paquete Dashboard y Analítica Criminal
            </p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight md:text-4xl">
              Overview analítico
            </h1>
            <p className="mt-2 max-w-xl text-sm text-slate-300">
              KPIs, gráficas dinámicas, mapas de calor y ranking — ISO 9241-210
            </p>
            {stats?.from_cache && (
              <span className="mt-3 inline-block rounded-lg bg-blue-500/20 px-2.5 py-1 text-xs text-blue-100">
                Datos en caché · {stats?.performance?.dashboard_query_ms} ms
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => setTab(id)}
                className={`flex cursor-pointer items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition ${
                  tab === id
                    ? 'bg-white text-slate-900 shadow-lg'
                    : 'bg-white/10 text-white hover:bg-white/20'
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Hechos delictivos" value={t.fact_crimes} sub="MinIO · fact_crimes" icon={Shield} />
        <KpiCard
          label="Casos"
          value={t.dim_caso}
          sub="dim_caso"
          icon={Activity}
          accent="from-violet-600 to-purple-600"
        />
        <KpiCard
          label="Tipos de crimen"
          value={t.dim_tipo_crimen}
          sub="Catálogo IUCR"
          icon={Database}
          accent="from-emerald-500 to-teal-600"
        />
        <KpiCard
          label="Dataset raw"
          value={t.crimes_220k}
          sub="PocketBase staging"
          icon={Database}
          accent="from-slate-600 to-slate-800"
        />
      </div>

      {tab === 'resumen' && (
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="border-0 bg-white/90 p-6 shadow-xl shadow-slate-200/50 backdrop-blur lg:col-span-2">
            <h3 className="font-semibold text-slate-900">Registros por dimensión</h3>
            <p className="text-sm text-slate-500">Modelo estrella · DuckDB</p>
            <div className="mt-4 h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartDims} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="label" tick={{ fontSize: 10 }} angle={-28} textAnchor="end" height={56} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0' }}
                    formatter={(v) => [Number(v).toLocaleString('es-CO'), 'Registros']}
                  />
                  <Bar dataKey="value" fill="url(#barGrad)" radius={[8, 8, 0, 0]} />
                  <defs>
                    <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#3b82f6" />
                      <stop offset="100%" stopColor="#6366f1" />
                    </linearGradient>
                  </defs>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card className="border-0 bg-white/90 p-6 shadow-xl shadow-slate-200/50 backdrop-blur">
            <h3 className="font-semibold text-slate-900">Top distritos</h3>
            <ul className="mt-4 max-h-72 space-y-2 overflow-y-auto">
              {byDistrict.map((d) => (
                <li
                  key={`${d.district}-${d.beat}`}
                  className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2 text-sm"
                >
                  <span>
                    D{d.district} · {d.beat}
                  </span>
                  <span className="font-mono text-xs font-semibold text-brand-600">
                    {Number(d.total_crimes).toLocaleString('es-CO')}
                  </span>
                </li>
              ))}
            </ul>
            {showCrud && (
              <Link to="/tabla/fact_crimes" className="mt-4 block">
                <Button className="w-full">Explorar hechos</Button>
              </Link>
            )}
          </Card>

          <Card className="border-0 bg-white/90 p-6 shadow-xl shadow-slate-200/50 backdrop-blur lg:col-span-3">
            <h3 className="font-semibold text-slate-900">Últimos hechos registrados</h3>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b text-xs uppercase tracking-wide text-slate-400">
                    <th className="pb-2 pr-4">Legacy</th>
                    <th className="pb-2 pr-4">Tipo</th>
                    <th className="pb-2 pr-4">Distrito</th>
                    <th className="pb-2">Año</th>
                  </tr>
                </thead>
                <tbody>
                  {(stats?.recent_facts || []).map((row) => (
                    <tr key={row.id} className="border-b border-slate-50 hover:bg-slate-50/80">
                      <td className="py-2.5 font-mono text-xs">{row.legacy_id ?? '—'}</td>
                      <td className="py-2.5">{row.expand?.tipo_crimen?.primary_type ?? '—'}</td>
                      <td className="py-2.5">{row.expand?.distrito?.district ?? '—'}</td>
                      <td className="py-2.5">{row.expand?.tiempo?.year ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {tab === 'filtros' && (
        <div className="space-y-6">
          <Card className="border-0 bg-white/90 p-6 shadow-lg backdrop-blur">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="font-semibold text-slate-900">Filtrar estadísticas</h3>
                <p className="text-sm text-slate-500">
                  Selecciona criterios del catálogo. Sin filtros se muestran todos los hechos.
                </p>
              </div>
              {hasActiveFilters && (
                <Badge tone="blue">Filtros activos</Badge>
              )}
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <FilterSelect
                label="Zona / distrito"
                value={filterDraft.zona}
                disabled={optionsLoading}
                onChange={(e) => setFilterDraft({ ...filterDraft, zona: e.target.value })}
              >
                <option value="">Todos los distritos</option>
                {(filterOptions.distritos || []).map((d) => (
                  <option key={d} value={d}>
                    Distrito {d}
                  </option>
                ))}
              </FilterSelect>
              <FilterSelect
                label="Tipo de delito"
                value={filterDraft.tipo}
                disabled={optionsLoading}
                onChange={(e) => setFilterDraft({ ...filterDraft, tipo: e.target.value })}
              >
                <option value="">Todos los tipos</option>
                {(filterOptions.tipos_delito || []).map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </FilterSelect>
              <FilterSelect
                label="Año"
                value={filterDraft.anio}
                disabled={optionsLoading}
                onChange={(e) => setFilterDraft({ ...filterDraft, anio: e.target.value })}
              >
                <option value="">Todos los años</option>
                {(filterOptions.anios || []).map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </FilterSelect>
              <FilterSelect
                label="Mes"
                value={filterDraft.mes}
                disabled={optionsLoading}
                onChange={(e) => setFilterDraft({ ...filterDraft, mes: e.target.value })}
              >
                <option value="">Todos los meses</option>
                {(filterOptions.meses || []).map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label || m.value}
                  </option>
                ))}
              </FilterSelect>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Button onClick={applyFilters} disabled={filtering || optionsLoading}>
                {filtering ? 'Cargando…' : 'Aplicar filtros'}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={clearFilters}
                disabled={filtering || !hasActiveFilters}
              >
                Limpiar filtros
              </Button>
            </div>
          </Card>

          {filtering && !filtered ? (
            <div className="flex justify-center py-12">
              <Spinner />
            </div>
          ) : filtered ? (
            <>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <KpiCard
                  label="Hechos en vista"
                  value={filtered.total_hechos}
                  sub={
                    hasActiveFilters
                      ? 'Con filtros aplicados'
                      : 'Vista inicial · sin filtros'
                  }
                  icon={Filter}
                />
                <KpiCard
                  label="Tipos en ranking"
                  value={(filtered.por_tipo || []).length}
                  sub="Top delitos en esta vista"
                  icon={BarChart3}
                  accent="from-violet-600 to-purple-600"
                />
                <KpiCard
                  label="Años con datos"
                  value={(filtered.por_anio || []).length}
                  sub="Tendencia temporal"
                  icon={TrendingUp}
                  accent="from-emerald-500 to-teal-600"
                />
                <KpiCard
                  label="Distritos"
                  value={(filtered.por_distrito || []).length}
                  sub="En el ranking actual"
                  icon={Map}
                  accent="from-slate-600 to-slate-800"
                />
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <Card className="border-0 bg-white/90 p-6 shadow-lg backdrop-blur">
                  <h4 className="font-semibold text-slate-900">Tendencia por año</h4>
                  <p className="text-sm text-slate-500">Hechos según criterios seleccionados</p>
                  <div className="mt-4 h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={filtered.por_anio || []}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Line
                          type="monotone"
                          dataKey="value"
                          stroke="#2563eb"
                          strokeWidth={2}
                          dot={{ r: 3 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </Card>

                <Card className="border-0 bg-white/90 p-6 shadow-lg backdrop-blur">
                  <h4 className="font-semibold text-slate-900">Por tipo de delito</h4>
                  <div className="mt-4 h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={(filtered.por_tipo || []).slice(0, 8)} layout="vertical" margin={{ left: 8 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis type="number" tick={{ fontSize: 11 }} />
                        <YAxis
                          type="category"
                          dataKey="label"
                          width={100}
                          tick={{ fontSize: 10 }}
                        />
                        <Tooltip />
                        <Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
              </div>

              <Card className="border-0 bg-white/90 p-6 shadow-lg backdrop-blur">
                <h4 className="font-semibold text-slate-900">Por distrito</h4>
                <ul className="mt-4 divide-y divide-slate-100">
                  {(filtered.por_distrito || []).slice(0, 10).map((r) => (
                    <li
                      key={`${r.district}-${r.beat}`}
                      className="flex items-center justify-between py-2.5 text-sm"
                    >
                      <span>
                        Distrito <strong>{r.district}</strong>
                        {r.beat ? ` · Beat ${r.beat}` : ''}
                      </span>
                      <span className="font-mono font-medium text-slate-800">
                        {Number(r.total_crimes).toLocaleString('es-CO')}
                      </span>
                    </li>
                  ))}
                </ul>
              </Card>
            </>
          ) : null}
        </div>
      )}

      {tab === 'mapa' && (
        <Card className="border-0 bg-white/90 p-6 shadow-xl backdrop-blur">
          <h3 className="font-semibold text-slate-900">Mapa de calor por distrito</h3>
          <p className="text-sm text-slate-500">Intensidad relativa de hechos delictivos</p>
          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {heatMap.map((z) => (
              <div
                key={`${z.district}-${z.beat}`}
                className="rounded-2xl border border-slate-100 p-4 transition hover:shadow-md"
                style={{
                  background: `linear-gradient(135deg, rgba(37,99,235,${0.08 + (z.intensity || 0) * 0.5}) 0%, rgba(99,102,241,0.05) 100%)`,
                }}
              >
                <p className="font-medium text-slate-800">{z.label}</p>
                <p className="mt-1 text-2xl font-bold text-slate-900">
                  {Number(z.total_crimes).toLocaleString('es-CO')}
                </p>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-600"
                    style={{ width: `${Math.min(100, (z.intensity || 0) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {tab === 'ranking' && (
        <Card className="border-0 bg-white/90 p-6 shadow-xl backdrop-blur">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="font-semibold text-slate-900">Ranking de detectives</h3>
              <p className="text-sm text-slate-500">Por casos asignados y resueltos · actualización automática</p>
            </div>
            {rankingLoading && <Spinner className="h-5 w-5" />}
          </div>
          <div className="mt-6 space-y-3">
            {ranking.map((d) => (
              <div
                key={d.fk_detective ?? d.detective}
                className="flex flex-wrap items-center gap-4 rounded-2xl border border-slate-100 bg-slate-50/80 px-4 py-3"
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-600 text-sm font-bold text-white">
                  {d.rank}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-slate-900">{d.detective}</p>
                  <p className="text-xs text-slate-500">
                    {d.casos_resueltos} resueltos / {d.casos_asignados} asignados
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-emerald-600">{d.tasa_resolucion}%</p>
                  <p className="text-xs text-slate-500">tasa resolución</p>
                </div>
              </div>
            ))}
            {ranking.length === 0 && !rankingLoading && (
              <p className="text-sm text-slate-500">Sin detectives con casos asignados activos.</p>
            )}
          </div>
        </Card>
      )}

      {tab === 'indicadores' && showIndicadores && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="border-0 bg-white/90 p-6 shadow-xl backdrop-blur">
            <h3 className="flex items-center gap-2 font-semibold text-slate-900">
              <TrendingUp className="h-5 w-5 text-brand-600" />
              Tendencias delictivas
            </h3>
            <div className="mt-4 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={3} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
          <Card className="border-0 bg-gradient-to-br from-emerald-50 to-teal-50 p-6 shadow-xl">
            <h3 className="font-semibold text-slate-900">Tasa de resolución</h3>
            <p className="mt-6 text-6xl font-bold text-emerald-600">
              {operational?.tasa_resolucion?.porcentaje ?? 0}%
            </p>
            <p className="mt-2 text-sm text-slate-600">
              {operational?.tasa_resolucion?.casos_resueltos?.toLocaleString('es-CO')} casos resueltos de{' '}
              {operational?.tasa_resolucion?.total_casos?.toLocaleString('es-CO')}
            </p>
          </Card>
        </div>
      )}
    </section>
  )
}
