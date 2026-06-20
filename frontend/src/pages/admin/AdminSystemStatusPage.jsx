import { useEffect, useState } from 'react'
import { Activity, RefreshCw, Server, Database, HardDrive } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Button, Card, Badge, Spinner } from '../../components/ui'

const COMPONENT_ICONS = {
  PocketBase: Database,
  MinIO: HardDrive,
  Redis: Server,
}

function StatusKpi({ label, value, sub, tone = 'slate' }) {
  const toneMap = {
    green: 'from-emerald-500 to-teal-600',
    blue: 'from-brand-600 to-indigo-600',
    slate: 'from-slate-500 to-slate-600',
    red: 'from-red-500 to-rose-600',
  }
  return (
    <Card className="relative overflow-hidden">
      <div
        className={`absolute -right-4 -top-4 h-20 w-20 rounded-full bg-gradient-to-br ${toneMap[tone]} opacity-10 blur-2xl`}
      />
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-bold capitalize tracking-tight text-slate-900">{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
    </Card>
  )
}

export default function AdminSystemStatusPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    adminApi
      .estadoSistema()
      .then(setData)
      .finally(() => setLoading(false))
  }
  useEffect(() => {
    load()
  }, [])

  const generalTone =
    data?.estado_general === 'operativo'
      ? 'green'
      : data?.estado_general === 'degradado'
        ? 'blue'
        : 'slate'

  return (
    <AdminGuard>
      <AdminPageHeader
        title="Estado del sistema"
        subtitle="Supervisión de PocketBase, MinIO, Redis y datasets"
        icon={Activity}
      >
        <Button type="button" variant="secondary" onClick={load} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </AdminPageHeader>
      {loading ? (
        <div className="flex justify-center py-20">
          <Spinner />
        </div>
      ) : (
        data && (
          <div className="space-y-6">
            <StatusKpi
              label="Estado general"
              value={data.estado_general}
              sub={data.timestamp}
              tone={generalTone}
            />
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {data.componentes?.map((c) => {
                const Icon = COMPONENT_ICONS[c.nombre] || Server
                const operativo = c.estado === 'operativo'
                return (
                  <Card key={c.nombre} className="group relative overflow-hidden transition hover:shadow-md">
                    <div
                      className={`absolute -right-4 -top-4 h-16 w-16 rounded-full bg-gradient-to-br ${
                        operativo ? 'from-emerald-500 to-teal-600' : 'from-slate-400 to-slate-500'
                      } opacity-10 blur-xl transition group-hover:opacity-20`}
                    />
                    <div className="relative flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold text-slate-900">{c.nombre}</p>
                        <div className="mt-2">
                          <Badge tone={operativo ? 'green' : 'slate'}>{c.estado}</Badge>
                        </div>
                        <p className="mt-2 truncate text-xs text-slate-500">{c.detalle}</p>
                      </div>
                      <div
                        className={`rounded-xl p-2.5 ${
                          operativo
                            ? 'bg-emerald-50 text-emerald-600'
                            : 'bg-slate-100 text-slate-500'
                        }`}
                      >
                        <Icon className="h-5 w-5" />
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
            <Card className="overflow-hidden p-0">
              <div className="border-b border-slate-100 bg-slate-50/80 px-5 py-3">
                <h3 className="text-sm font-semibold text-slate-900">Datasets</h3>
              </div>
              <ul className="divide-y divide-slate-100">
                {Object.entries(data.datasets || {}).map(([k, v]) => (
                  <li
                    key={k}
                    className="flex items-center justify-between px-5 py-3 text-sm transition hover:bg-slate-50/60"
                  >
                    <span className="font-medium text-slate-700">{k}</span>
                    <Badge tone="blue">{v}</Badge>
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        )
      )}
    </AdminGuard>
  )
}
