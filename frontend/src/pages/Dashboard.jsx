import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useSearchParams } from 'react-router-dom'
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
  TrendingUp,
  Users,
  Shield,
  Database,
  Briefcase,
  Tags,
} from 'lucide-react'
import { dashboardApi } from '../api/dashboard'
import Combobox from '../components/ui/Combobox'
import { useAuth } from '../context/AuthContext'
import { useAppConfig } from '../context/AppConfigContext'
import { useToast } from '../context/ToastContext'
import { CACHE_KEYS, readSessionCache, writeSessionCache } from '../lib/sessionCache'
import { aggregateRowKey, rollupByDistrict } from '../utils/aggregateRowKey'
import {
  dashboardFiltersToApi,
  EMPTY_DASHBOARD_FILTERS,
  hasDashboardFilters,
} from '../utils/dashboardFilters'
import { canAccessDataCrud, canViewDashboard, canViewInvestigacionProgress, canViewOperationalIndicators } from '../utils/roles'
import { Badge, Button, Card, Spinner } from '../components/ui'
import PageHeader from '../components/layout/PageHeader'
import StatCard from '../components/layout/StatCard'

const TABS = [
  { id: 'resumen', label: 'Resumen', icon: BarChart3 },
  { id: 'filtros', label: 'Filtros', icon: Filter },
  { id: 'mapa', label: 'Mapa de calor', icon: Map },
  { id: 'ranking', label: 'Ranking', icon: Users },
  { id: 'indicadores', label: 'Indicadores', icon: Activity, analistaOnly: true },
]

function FilterMonthField({ label, value, onChange, disabled }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-bold text-black">{label}</span>
      <input
        type="month"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="input-field cursor-pointer font-normal disabled:cursor-not-allowed disabled:opacity-60"
        aria-label={label}
      />
    </label>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const { comboboxVisibleCount } = useAppConfig()
  const toast = useToast()
  const showCrud = canAccessDataCrud(user)
  const showIndicadores = canViewOperationalIndicators(user)
  const canView = canViewDashboard(user)

  const [searchParams, setSearchParams] = useSearchParams()
  const tabFromUrl = searchParams.get('tab')
  const cachedOverview = useMemo(
    () => (canView ? readSessionCache(CACHE_KEYS.dashboardOverview) : null),
    [canView]
  )
  const [stats, setStats] = useState(cachedOverview)
  const [loading, setLoading] = useState(!cachedOverview)
  const [refreshing, setRefreshing] = useState(false)
  const [filterDraft, setFilterDraft] = useState(EMPTY_DASHBOARD_FILTERS)
  const [filterOptions, setFilterOptions] = useState({
    distritos: [],
    tipos_delito: [],
  })
  const [filtered, setFiltered] = useState(null)
  const [filtering, setFiltering] = useState(false)
  const [optionsLoading, setOptionsLoading] = useState(true)
  const [ranking, setRanking] = useState([])
  const [rankingLoading, setRankingLoading] = useState(false)

  const tabs = useMemo(
    () => TABS.filter((t) => !t.analistaOnly || showIndicadores),
    [showIndicadores]
  )

  const tab = tabs.some((t) => t.id === tabFromUrl) ? tabFromUrl : 'resumen'

  const setTab = (id) => {
    if (!id || id === 'resumen') {
      setSearchParams({})
    } else {
      setSearchParams({ tab: id })
    }
  }

  const loadOverview = useCallback(async ({ background = false } = {}) => {
    if (!canView) return
    if (background) {
      setRefreshing(true)
    } else {
      setLoading(true)
    }
    try {
      const data = await dashboardApi.overview()
      setStats(data)
      writeSessionCache(CACHE_KEYS.dashboardOverview, data)
    } catch (e) {
      if (!background) {
        toast.error('Error', e.message || 'No se pudo cargar el dashboard')
      }
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [toast, canView])

  useEffect(() => {
    if (!canView) return
    loadOverview({ background: Boolean(cachedOverview) })
  }, [canView, loadOverview, cachedOverview])

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

  const fetchFilteredStats = useCallback(
    async (draft, { silent = false } = {}) => {
      const params = dashboardFiltersToApi(draft)
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
    },
    [toast]
  )

  useEffect(() => {
    if (!canView || tab !== 'filtros') return
    let cancelled = false
    const cachedOptions = readSessionCache(CACHE_KEYS.dashboardFilterOptions)
    const cachedFiltered = readSessionCache(CACHE_KEYS.dashboardFilteredEmpty)
    if (cachedOptions) setFilterOptions(cachedOptions)
    if (cachedFiltered) setFiltered(cachedFiltered)
    if (cachedOptions && cachedFiltered) setOptionsLoading(false)

    ;(async () => {
      if (!cachedOptions || !cachedFiltered) setOptionsLoading(true)
      try {
        const [opts, filteredData] = await Promise.all([
          dashboardApi.filtrosOpciones(),
          dashboardApi.filtros(dashboardFiltersToApi(EMPTY_DASHBOARD_FILTERS)),
        ])
        if (!cancelled) {
          setFilterOptions(opts)
          setFiltered(filteredData)
          writeSessionCache(CACHE_KEYS.dashboardFilterOptions, opts)
          writeSessionCache(CACHE_KEYS.dashboardFilteredEmpty, filteredData)
        }
      } catch (e) {
        if (!cancelled) toast.error('Error', e.message || 'No se cargaron opciones de filtro')
      } finally {
        if (!cancelled) setOptionsLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [toast, canView, tab])

  const applyFilters = async () => {
    await fetchFilteredStats(filterDraft)
    setTab('filtros')
  }

  const clearFilters = async () => {
    setFilterDraft(EMPTY_DASHBOARD_FILTERS)
    await fetchFilteredStats(EMPTY_DASHBOARD_FILTERS, { silent: true })
  }

  const hasActiveFilters = hasDashboardFilters(filterDraft)

  const distritoOptions = useMemo(
    () => [
      { value: '', label: 'Todos los distritos' },
      ...(filterOptions.distritos || []).map((d) => ({
        value: d,
        label: `Distrito ${d}`,
      })),
    ],
    [filterOptions.distritos]
  )

  const tipoOptions = useMemo(
    () => [
      { value: '', label: 'Todos los tipos' },
      ...(filterOptions.tipos_delito || []).map((t) => ({ value: t, label: t })),
    ],
    [filterOptions.tipos_delito]
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
  const byDistrict = rollupByDistrict(
    (stats?.crimes_by_district?.items || []).map((d) => ({
      district: d.district,
      beat: d.beat,
      total: d.total_crimes,
    }))
  )
  const byType = stats?.crimes_by_type || []
  const heatMap = stats?.heat_map || []
  const operational = stats?.operational_indicators || {}
  const trend = operational?.tendencias_delictivas || []

  return (
    <section className="space-y-6 animate-fade-up">
      <PageHeader
        title="Panel de control"
        subtitle="Centro de comando · Analítica criminal en tiempo real"
        icon={BarChart3}
        badge={
          stats?.from_cache || refreshing ? (
            <span className="code-badge">
              {refreshing ? 'Actualizando…' : 'Caché'}{' '}
              {stats?.performance?.dashboard_query_ms != null
                ? `· ${stats.performance.dashboard_query_ms} ms`
                : ''}
            </span>
          ) : null
        }
      />

      <div className="tab-bar">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={cnTab(tab === id)}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Hechos delictivos" value={(t.fact_crimes ?? 0).toLocaleString('es-CO')} sub="MinIO · fact_crimes" sparkline="blue" icon={Shield} />
        <StatCard label="Casos" value={(t.dim_caso ?? 0).toLocaleString('es-CO')} sub="dim_caso" sparkline="purple" icon={Briefcase} />
        <StatCard label="Tipos de crimen" value={(t.dim_tipo_crimen ?? 0).toLocaleString('es-CO')} sub="Catálogo IUCR" sparkline="green" icon={Tags} />
        <StatCard label="Dataset raw" value={(t.crimes_220k ?? 0).toLocaleString('es-CO')} sub="PocketBase staging" sparkline="blue" icon={Database} />
      </div>

      {tab === 'resumen' && (
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <h3 className="section-title">Registros por dimensión</h3>
            <p className="section-subtitle">Modelo estrella · DuckDB</p>
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

          <Card>
            <h3 className="section-title">Top distritos</h3>
            <ul className="mt-4 max-h-72 space-y-2 overflow-y-auto">
              {byDistrict.map((d, i) => (
                <li
                  key={aggregateRowKey({ district: d.district, beat: d.beat }, i)}
                  className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2.5 text-sm transition hover:bg-indigo-50/50 dark:bg-slate-800/50 dark:hover:bg-indigo-950/30"
                >
                  <span className="text-slate-700 dark:text-slate-300">
                    D{d.district} · {d.beat}
                  </span>
                  <span className="font-mono text-xs font-semibold text-indigo-600 dark:text-indigo-400">
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

          <Card className="lg:col-span-3">
            <h3 className="section-title">Últimos hechos registrados</h3>
            <div className="mt-4 overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Legacy</th>
                    <th>Tipo</th>
                    <th>Distrito</th>
                    <th>Año</th>
                  </tr>
                </thead>
                <tbody>
                  {(stats?.recent_facts || []).map((row) => (
                    <tr key={row.id}>
                      <td className="font-mono text-xs">{row.legacy_id ?? '—'}</td>
                      <td>{row.expand?.tipo_crimen?.primary_type ?? '—'}</td>
                      <td>{row.expand?.distrito?.district ?? '—'}</td>
                      <td>{row.expand?.tiempo?.year ?? '—'}</td>
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
          <Card className="overflow-visible border-0 bg-white/90 p-6 shadow-lg backdrop-blur">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="section-title">Filtrar estadísticas</h3>
                <p className="section-subtitle">
                  Selecciona criterios del catálogo. Sin filtros se muestran todos los hechos.
                </p>
              </div>
              {hasActiveFilters && (
                <Badge tone="blue">Filtros activos</Badge>
              )}
            </div>
            <div className="grid gap-3 overflow-visible sm:grid-cols-2 lg:grid-cols-3">
              <Combobox
                label="Zona / distrito"
                value={filterDraft.zona}
                disabled={optionsLoading}
                visibleCount={comboboxVisibleCount}
                placeholder="Todos los distritos"
                options={distritoOptions}
                onChange={(zona) => setFilterDraft({ ...filterDraft, zona })}
              />
              <Combobox
                label="Tipo de delito"
                value={filterDraft.tipo}
                disabled={optionsLoading}
                visibleCount={comboboxVisibleCount}
                placeholder="Todos los tipos"
                options={tipoOptions}
                onChange={(tipo) => setFilterDraft({ ...filterDraft, tipo })}
              />
              <FilterMonthField
                label="Fecha (año y mes)"
                value={filterDraft.fecha}
                disabled={optionsLoading}
                onChange={(fecha) => setFilterDraft({ ...filterDraft, fecha })}
              />
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-3">
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
                <StatCard
                  label="Hechos en vista"
                  value={(filtered.total_hechos ?? 0).toLocaleString('es-CO')}
                  sub={hasActiveFilters ? 'Con filtros aplicados' : 'Vista inicial · sin filtros'}
                  sparkline="blue"
                />
                <StatCard
                  label="Tipos en ranking"
                  value={(filtered.por_tipo || []).length}
                  sub="Top delitos en esta vista"
                  sparkline="purple"
                />
                <StatCard
                  label="Años con datos"
                  value={(filtered.por_anio || []).length}
                  sub="Tendencia temporal"
                  sparkline="green"
                />
                <StatCard
                  label="Distritos"
                  value={(filtered.por_distrito || []).length}
                  sub="En el ranking actual"
                  sparkline="blue"
                />
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <Card className="border-0 bg-white/90 p-6 shadow-lg backdrop-blur">
                  <h4 className="section-title">Tendencia por año</h4>
                  <p className="section-subtitle">Hechos según criterios seleccionados</p>
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
                  <h4 className="section-title">Por tipo de delito</h4>
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
                <h4 className="section-title">Por distrito</h4>
                <ul className="mt-4 divide-y divide-slate-100">
                  {(filtered.por_distrito || []).slice(0, 10).map((r, i) => (
                    <li
                      key={aggregateRowKey({ district: r.district, beat: r.beat }, i)}
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
          <h3 className="section-title">Mapa de calor por distrito</h3>
          <p className="section-subtitle">Intensidad relativa de hechos delictivos</p>
          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {heatMap.map((z, i) => (
              <div
                key={aggregateRowKey({ district: z.district, beat: z.beat }, i)}
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
              <h3 className="section-title">Ranking de detectives</h3>
              <p className="section-subtitle">Por casos asignados y resueltos · actualización automática</p>
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
                  <p className="section-title">{d.detective}</p>
                  <p className="caption-text">
                    {d.casos_resueltos} resueltos / {d.casos_asignados} asignados
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-emerald-600">{d.tasa_resolucion}%</p>
                  <p className="caption-text">tasa resolución</p>
                </div>
              </div>
            ))}
            {ranking.length === 0 && !rankingLoading && (
              <p className="section-subtitle">Sin detectives con casos asignados activos.</p>
            )}
          </div>
        </Card>
      )}

      {tab === 'indicadores' && showIndicadores && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="border-0 bg-white/90 p-6 shadow-xl backdrop-blur">
            <h3 className="flex items-center gap-2 section-title">
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
            <h3 className="section-title">Tasa de resolución</h3>
            <p className="mt-6 text-6xl font-bold text-emerald-600">
              {operational?.tasa_resolucion?.porcentaje ?? 0}%
            </p>
            <p className="mt-2 body-text">
              {operational?.tasa_resolucion?.casos_resueltos?.toLocaleString('es-CO')} casos resueltos de{' '}
              {operational?.tasa_resolucion?.total_casos?.toLocaleString('es-CO')}
            </p>
          </Card>
        </div>
      )}
    </section>
  )
}

function cnTab(active) {
  return `tab-pill ${active ? 'tab-pill--active' : ''}`
}
