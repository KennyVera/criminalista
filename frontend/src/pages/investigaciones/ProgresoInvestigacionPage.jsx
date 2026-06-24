import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ClipboardList,
  Bell,
  ChevronRight,
  TrendingUp,
  FolderOpen,
  Search,
  Users,
  ArrowLeft,
  Briefcase,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { asignacionesApi } from '../../api/asignaciones'
import { Card, Badge, Spinner } from '../../components/ui'
import { useToast } from '../../context/ToastContext'
import { canViewInvestigacionProgress, isDetective } from '../../utils/roles'
import { Navigate } from 'react-router-dom'

function ProgressBar({ percent }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200/80">
      <div
        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-blue-600 transition-all shadow-sm"
        style={{ width: `${Math.min(100, percent)}%` }}
      />
    </div>
  )
}

function StatCard({ label, value, icon: Icon, accent = 'from-indigo-600 to-blue-700' }) {
  return (
    <Card className="glass-card relative overflow-hidden p-5 text-center">
      <div
        className={`absolute -right-4 -top-4 h-20 w-20 rounded-full bg-gradient-to-br ${accent} opacity-15 blur-xl`}
      />
      <div className="relative">
        <div className={`mx-auto mb-2 inline-flex rounded-xl bg-gradient-to-br ${accent} p-2 text-white shadow-md`}>
          <Icon className="h-4 w-4" />
        </div>
        <p className="text-2xl font-bold tracking-tight text-slate-900">{value}</p>
        <p className="mt-0.5 text-xs font-medium text-slate-500">{label}</p>
      </div>
    </Card>
  )
}

function ExpedienteCard({ item }) {
  return (
    <Link
      to={`/expedientes/${encodeURIComponent(item.case_number)}`}
      className="group block rounded-xl transition-all hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
    >
      <Card className="glass-card p-5 transition-shadow group-hover:shadow-xl group-hover:shadow-indigo-500/10">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="font-semibold tracking-tight text-slate-900">{item.case_number}</p>
            <p className="text-sm text-slate-500">
              {item.detective_nombre} · Placa {item.detective_placa}
            </p>
            <p className="mt-1 text-xs text-slate-400">Asignado: {item.fecha_asignacion}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge>{item.estado_caso}</Badge>
            <Badge tone={item.prioridad_caso === 'Crítica' ? 'red' : 'gray'}>
              {item.prioridad_caso}
            </Badge>
            {item.notificado && (
              <Badge tone="green">
                <Bell className="mr-1 inline h-3 w-3" />
                Notificado
              </Badge>
            )}
          </div>
        </div>
        <div className="mt-4">
          <div className="mb-1.5 flex justify-between text-xs font-medium text-slate-500">
            <span>Avance de investigación</span>
            <span className="text-indigo-600">{item.avance_pct}%</span>
          </div>
          <ProgressBar percent={item.avance_pct} />
        </div>
        {item.observaciones && (
          <p className="mt-3 rounded-lg bg-slate-50/80 px-3 py-2 text-xs text-slate-600">
            {item.observaciones}
          </p>
        )}
        <p className="mt-3 flex items-center gap-1 text-xs font-semibold text-indigo-600 transition group-hover:text-indigo-700">
          Ver expediente
          <ChevronRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
        </p>
      </Card>
    </Link>
  )
}

function DetectiveCard({ grupo, onSelect }) {
  const cargaTone =
    grupo.casos <= 3
      ? 'from-emerald-500 to-teal-600'
      : grupo.casos < 8
        ? 'from-amber-500 to-orange-500'
        : 'from-rose-500 to-red-600'
  return (
    <button
      type="button"
      onClick={onSelect}
      className="group block w-full text-left transition-all hover:-translate-y-0.5 focus:outline-none"
    >
      <Card className="glass-card p-5 transition-shadow group-hover:shadow-xl group-hover:shadow-indigo-500/10">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div
              className={`inline-flex rounded-xl bg-gradient-to-br ${cargaTone} p-2.5 text-white shadow-md`}
            >
              <Users className="h-5 w-5" />
            </div>
            <div>
              <p className="font-semibold tracking-tight text-slate-900">{grupo.nombre}</p>
              <p className="text-xs text-slate-500">Placa {grupo.placa}</p>
            </div>
          </div>
          <ChevronRight className="h-5 w-5 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-indigo-500" />
        </div>
        <div className="mt-4 flex items-center justify-between text-sm">
          <span className="inline-flex items-center gap-1.5 font-medium text-slate-700">
            <Briefcase className="h-4 w-4 text-indigo-500" />
            {grupo.casos} expediente(s) asignado(s)
          </span>
          <span className="text-xs font-semibold text-indigo-600">
            Avance prom. {grupo.avgAvance}%
          </span>
        </div>
        <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-200/80">
          <div
            className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-blue-600"
            style={{ width: `${grupo.avgAvance}%` }}
          />
        </div>
      </Card>
    </button>
  )
}

export default function ProgresoInvestigacionPage() {
  const { user } = useAuth()
  const toast = useToast()
  const [data, setData] = useState({ items: [], resumen: {} })
  const [loading, setLoading] = useState(true)
  const [selectedDet, setSelectedDet] = useState(null)
  const allowed = canViewInvestigacionProgress(user)
  const soloMios = isDetective(user)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await asignacionesApi.progreso(soloMios)
      setData(res)
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setLoading(false)
    }
  }, [soloMios, toast])

  useEffect(() => {
    if (allowed) load()
  }, [allowed, load])

  const { items = [], resumen = {} } = data

  // Agrupa por detective (para Comisario/Admin): carga laboral por persona.
  const grupos = useMemo(() => {
    const map = new Map()
    for (const it of items) {
      const key = it.fk_detective ?? it.detective_nombre
      if (!map.has(key)) {
        map.set(key, {
          fk_detective: it.fk_detective,
          nombre: it.detective_nombre,
          placa: it.detective_placa,
          items: [],
        })
      }
      map.get(key).items.push(it)
    }
    return Array.from(map.values())
      .map((g) => ({
        ...g,
        casos: g.items.length,
        avgAvance: Math.round(
          g.items.reduce((s, x) => s + (x.avance_pct || 0), 0) / (g.items.length || 1),
        ),
      }))
      .sort((a, b) => b.casos - a.casos)
  }, [items])

  if (!allowed) return <Navigate to="/" replace />

  const grupoSel = grupos.find((g) => (g.fk_detective ?? g.nombre) === selectedDet)

  return (
    <section className="mx-auto max-w-5xl space-y-8">
      <header className="page-header">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-gradient-to-br from-indigo-600 to-blue-700 p-3 text-white shadow-lg shadow-indigo-500/25">
            <Search className="h-6 w-6" />
          </div>
          <div>
            <h2>
              {soloMios ? 'Mis expedientes asignados' : 'Progreso de investigaciones'}
            </h2>
            <p>
              Supervise el avance de los expedientes activos y el estado de las asignaciones del
              equipo investigativo.
            </p>
          </div>
        </div>
      </header>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Expedientes activos"
          value={resumen.total ?? 0}
          icon={FolderOpen}
        />
        <StatCard
          label="En investigación"
          value={resumen.en_investigacion ?? 0}
          icon={TrendingUp}
          accent="from-blue-600 to-cyan-600"
        />
        <StatCard
          label="Notificados"
          value={items.filter((i) => i.notificado).length}
          icon={Bell}
          accent="from-emerald-600 to-teal-600"
        />
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : items.length === 0 ? (
        <Card className="glass-card p-10 text-center">
          <ClipboardList className="mx-auto mb-3 h-10 w-10 text-slate-300" />
          <p className="text-sm font-medium text-slate-600">Sin expedientes activos</p>
          <p className="mt-1 text-xs text-slate-500">
            No hay investigaciones asignadas en este momento.
          </p>
        </Card>
      ) : soloMios ? (
        // Detective: ve directamente sus propios expedientes.
        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.id_asignacion}>
              <ExpedienteCard item={item} />
            </li>
          ))}
        </ul>
      ) : grupoSel ? (
        // Carga laboral de un detective seleccionado.
        <div className="space-y-4">
          <button
            type="button"
            onClick={() => setSelectedDet(null)}
            className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-sm font-medium text-indigo-600 transition hover:bg-indigo-50 hover:text-indigo-700"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver al equipo
          </button>
          <div className="flex items-center gap-3">
            <div className="inline-flex rounded-xl bg-gradient-to-br from-indigo-600 to-blue-700 p-2.5 text-white shadow-md">
              <Users className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold tracking-tight text-slate-900">
                {grupoSel.nombre}
              </h3>
              <p className="text-xs text-slate-500">
                Placa {grupoSel.placa} · {grupoSel.casos} expediente(s) asignado(s)
              </p>
            </div>
          </div>
          <ul className="space-y-3">
            {grupoSel.items.map((item) => (
              <li key={item.id_asignacion}>
                <ExpedienteCard item={item} />
              </li>
            ))}
          </ul>
        </div>
      ) : (
        // Comisario/Admin: lista de detectives con su carga laboral.
        <div className="space-y-3">
          <p className="text-sm font-medium text-slate-500">
            Seleccione un detective para ver sus expedientes asignados (carga laboral).
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            {grupos.map((g) => (
              <DetectiveCard
                key={g.fk_detective ?? g.nombre}
                grupo={g}
                onSelect={() => setSelectedDet(g.fk_detective ?? g.nombre)}
              />
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
