import { useEffect, useState } from 'react'
import { Activity, RefreshCw } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Button, Card, Badge, Spinner } from '../../components/ui'

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

  return (
    <AdminGuard>
      <AdminPageHeader
        title="Estado del sistema"
        subtitle="Supervisión de PocketBase, MinIO, Redis y datasets"
        icon={Activity}
      >
        <Button type="button" variant="secondary" onClick={load}>
          <RefreshCw className="h-4 w-4" />
          Actualizar
        </Button>
      </AdminPageHeader>
      {loading ? (
        <Spinner />
      ) : (
        data && (
          <div className="space-y-6">
            <Card>
              <p className="text-sm text-slate-500">Estado general</p>
              <p className="mt-1 text-2xl font-bold capitalize">{data.estado_general}</p>
              <p className="text-xs text-slate-400">{data.timestamp}</p>
            </Card>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {data.componentes?.map((c) => (
                <Card key={c.nombre}>
                  <p className="font-medium">{c.nombre}</p>
                  <Badge tone={c.estado === 'operativo' ? 'green' : 'slate'} className="mt-2">
                    {c.estado}
                  </Badge>
                  <p className="mt-2 truncate text-xs text-slate-500">{c.detalle}</p>
                </Card>
              ))}
            </div>
            <Card>
              <h3 className="mb-3 font-semibold">Datasets</h3>
              <ul className="grid gap-2 sm:grid-cols-2">
                {Object.entries(data.datasets || {}).map(([k, v]) => (
                  <li key={k} className="flex justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
                    <span>{k}</span>
                    <strong>{v}</strong>
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
