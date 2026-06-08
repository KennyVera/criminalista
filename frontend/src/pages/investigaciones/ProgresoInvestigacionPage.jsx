import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ClipboardList, Bell, ChevronRight } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { asignacionesApi } from '../../api/asignaciones'
import { Card, Badge, Spinner } from '../../components/ui'
import { useToast } from '../../context/ToastContext'
import { canViewInvestigacionProgress, isDetective } from '../../utils/roles'
import { Navigate } from 'react-router-dom'

function ProgressBar({ percent }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
      <div
        className="h-full rounded-full bg-brand-500 transition-all"
        style={{ width: `${Math.min(100, percent)}%` }}
      />
    </div>
  )
}

export default function ProgresoInvestigacionPage() {
  const { user } = useAuth()
  const toast = useToast()
  const [data, setData] = useState({ items: [], resumen: {} })
  const [loading, setLoading] = useState(true)
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

  if (!allowed) return <Navigate to="/" replace />

  const { items = [], resumen = {} } = data

  return (
    <section className="mx-auto max-w-5xl space-y-6">
      <header>
        <h2 className="text-xl font-bold text-slate-900">
          {soloMios ? 'Mis expedientes asignados' : 'Progreso de investigaciones'}
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Expedientes asignados y supervisión del avance investigativo.
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="p-4 text-center">
          <p className="text-2xl font-bold text-slate-900">{resumen.total ?? 0}</p>
          <p className="text-xs text-slate-500">Expedientes activos</p>
        </Card>
        <Card className="p-4 text-center">
          <p className="text-2xl font-bold text-brand-600">{resumen.en_investigacion ?? 0}</p>
          <p className="text-xs text-slate-500">En investigación</p>
        </Card>
        <Card className="p-4 text-center">
          <p className="text-2xl font-bold text-slate-700">
            {items.filter((i) => i.notificado).length}
          </p>
          <p className="text-xs text-slate-500">Notificados</p>
        </Card>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : items.length === 0 ? (
        <Card className="p-8 text-center text-sm text-slate-500">
          <ClipboardList className="mx-auto mb-2 h-8 w-8 text-slate-300" />
          No hay expedientes asignados activos.
        </Card>
      ) : (
        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.id_asignacion}>
              <Link
                to={`/expedientes/${encodeURIComponent(item.case_number)}`}
                className="block rounded-2xl transition-shadow hover:shadow-md focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
              <Card className="p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold text-slate-900">{item.case_number}</p>
                    <p className="text-sm text-slate-500">
                      {item.detective_nombre} · Placa {item.detective_placa}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      Asignado: {item.fecha_asignacion}
                    </p>
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
                <div className="mt-3">
                  <div className="mb-1 flex justify-between text-xs text-slate-500">
                    <span>Avance registrado</span>
                    <span>{item.avance_pct}%</span>
                  </div>
                  <ProgressBar percent={item.avance_pct} />
                </div>
                {item.observaciones && (
                  <p className="mt-2 text-xs text-slate-600">{item.observaciones}</p>
                )}
                <p className="mt-3 flex items-center gap-1 text-xs font-medium text-brand-600">
                  Abrir expediente
                  <ChevronRight className="h-4 w-4" />
                </p>
              </Card>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
