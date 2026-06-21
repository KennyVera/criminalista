import { useCallback, useEffect, useMemo, useState } from 'react'
import { Navigate } from 'react-router-dom'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { TrendingUp, TrendingDown, Minus, Sparkles, Gauge, CalendarRange } from 'lucide-react'
import { dashboardApi } from '../api/dashboard'
import { Card, Spinner } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { canViewOperationalIndicators } from '../utils/roles'

const HORIZONTES = [3, 6, 9, 12]

const TENDENCIA_META = {
  creciente: { label: 'Tendencia creciente', icon: TrendingUp, color: 'text-rose-600', bg: 'bg-rose-50 border-rose-200' },
  decreciente: { label: 'Tendencia decreciente', icon: TrendingDown, color: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-200' },
  estable: { label: 'Tendencia estable', icon: Minus, color: 'text-slate-600', bg: 'bg-slate-50 border-slate-200' },
}

export default function PrediccionPage() {
  const { user } = useAuth()
  const toast = useToast()
  const allowed = canViewOperationalIndicators(user)

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [horizonte, setHorizonte] = useState(6)
  const [zona, setZona] = useState('')
  const [tipo, setTipo] = useState('')
  const [opciones, setOpciones] = useState({ distritos: [], tipos_delito: [] })

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await dashboardApi.prediccion({ horizonte, zona, tipo })
      setData(res)
    } catch (err) {
      toast.error('Predicción', err.message)
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [horizonte, zona, tipo, toast])

  useEffect(() => {
    if (!allowed) return
    dashboardApi
      .filtrosOpciones()
      .then((o) => setOpciones({ distritos: o.distritos || [], tipos_delito: o.tipos_delito || [] }))
      .catch(() => {})
  }, [allowed])

  useEffect(() => {
    if (allowed) load()
  }, [allowed, load])

  const chartData = useMemo(() => {
    if (!data?.disponible) return []
    const hist = (data.historico || []).map((h) => ({ label: h.label, real: h.valor }))
    if (hist.length) {
      const last = hist[hist.length - 1]
      last.pred = last.real
      last.banda = [last.real, last.real]
    }
    const pred = (data.prediccion || []).map((p) => ({
      label: p.label,
      pred: p.valor,
      banda: [p.min, p.max],
    }))
    return [...hist, ...pred]
  }, [data])

  if (!allowed) return <Navigate to="/" replace />

  const resumen = data?.resumen
  const modelo = data?.modelo
  const tMeta = TENDENCIA_META[resumen?.tendencia] || TENDENCIA_META.estable
  const TIcon = tMeta.icon

  return (
    <section className="mx-auto max-w-7xl space-y-8">
      <header className="page-header">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-gradient-to-br from-violet-600 to-indigo-700 p-3 text-white shadow-lg shadow-violet-500/25">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <h2>Predicción criminal</h2>
            <p>
              Proyección de la incidencia delictiva mensual mediante regresión de tendencia y
              componente estacional, con banda de confianza al 95%.
            </p>
          </div>
        </div>
      </header>

      <Card className="glass-card p-5">
        <div className="grid gap-4 sm:grid-cols-3">
          <label className="block text-sm font-medium text-slate-700">
            Horizonte de pronóstico
            <select
              value={horizonte}
              onChange={(e) => setHorizonte(Number(e.target.value))}
              className="input-field mt-1.5"
            >
              {HORIZONTES.map((h) => (
                <option key={h} value={h}>
                  {h} meses
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Distrito (opcional)
            <select value={zona} onChange={(e) => setZona(e.target.value)} className="input-field mt-1.5">
              <option value="">Todos los distritos</option>
              {opciones.distritos.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Tipo de delito (opcional)
            <select value={tipo} onChange={(e) => setTipo(e.target.value)} className="input-field mt-1.5">
              <option value="">Todos los tipos</option>
              {opciones.tipos_delito.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
        </div>
      </Card>

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : !data?.disponible ? (
        <Card className="glass-card p-8 text-center text-slate-600">
          {data?.motivo || 'No hay datos suficientes para generar una predicción.'}
        </Card>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className={`rounded-2xl border p-4 ${tMeta.bg}`}>
              <div className={`flex items-center gap-2 text-sm font-semibold ${tMeta.color}`}>
                <TIcon className="h-4 w-4" />
                {tMeta.label}
              </div>
              <p className="mt-1 text-2xl font-bold text-slate-900">
                {resumen.variacion_pct > 0 ? '+' : ''}
                {resumen.variacion_pct}%
              </p>
              <p className="text-xs text-slate-500">vs. promedio histórico</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white/80 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-600">
                <CalendarRange className="h-4 w-4" />
                Promedio pronosticado
              </div>
              <p className="mt-1 text-2xl font-bold text-slate-900">
                {resumen.promedio_mensual_pronosticado}
              </p>
              <p className="text-xs text-slate-500">hechos / mes</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white/80 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-600">
                <Gauge className="h-4 w-4" />
                Ajuste del modelo (R²)
              </div>
              <p className="mt-1 text-2xl font-bold text-slate-900">{modelo.r2}</p>
              <p className="text-xs text-slate-500">{modelo.meses_historicos} meses analizados</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white/80 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-600">
                <TrendingUp className="h-4 w-4" />
                Promedio histórico
              </div>
              <p className="mt-1 text-2xl font-bold text-slate-900">
                {resumen.promedio_mensual_historico}
              </p>
              <p className="text-xs text-slate-500">hechos / mes</p>
            </div>
          </div>

          <Card className="glass-card p-5">
            <div className="mb-4 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-violet-600" />
              <h3 className="font-semibold text-slate-900">
                Histórico y pronóstico ({modelo.horizonte_meses} meses)
              </h3>
            </div>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="label" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                  <Tooltip
                    formatter={(value, name) => {
                      if (name === 'banda') return [`${value[0]} – ${value[1]}`, 'Banda 95%']
                      return [value, name === 'real' ? 'Histórico' : 'Pronóstico']
                    }}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="banda"
                    name="Banda 95%"
                    stroke="none"
                    fill="#a78bfa"
                    fillOpacity={0.18}
                    connectNulls
                    legendType="none"
                  />
                  <Line
                    type="monotone"
                    dataKey="real"
                    name="Histórico"
                    stroke="#4f46e5"
                    strokeWidth={2.5}
                    dot={false}
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="pred"
                    name="Pronóstico"
                    stroke="#9333ea"
                    strokeWidth={2.5}
                    strokeDasharray="6 4"
                    dot={{ r: 2.5 }}
                    connectNulls
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-3 text-xs text-slate-500">
              Modelo: {modelo.tipo}. La banda sombreada representa el intervalo de confianza al{' '}
              {modelo.confianza}. Esta proyección es orientativa y debe interpretarse junto al
              criterio del analista.
            </p>
          </Card>
        </>
      )}
    </section>
  )
}
