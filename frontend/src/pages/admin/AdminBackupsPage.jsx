import { useEffect, useState } from 'react'
import { HardDrive } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Button, Card, Badge } from '../../components/ui'
import { useToast } from '../../context/ToastContext'

export default function AdminBackupsPage() {
  const [items, setItems] = useState([])
  const [running, setRunning] = useState(false)
  const toast = useToast()

  const load = () => adminApi.respaldos().then((d) => setItems(d.items || []))
  useEffect(() => {
    load()
  }, [])

  const ejecutar = async () => {
    setRunning(true)
    try {
      const r = await adminApi.runRespaldo()
      toast.success('Éxito', `Respaldo OK: ${r.tablas_copiadas} tablas en ${r.destino}`)
      load()
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setRunning(false)
    }
  }

  return (
    <AdminGuard>
      <AdminPageHeader
        title="Configurar respaldos"
        subtitle="Copias de tablas transaccionales hacia MinIO"
        icon={HardDrive}
      >
        <Button type="button" onClick={ejecutar} disabled={running}>
          {running ? 'Ejecutando...' : 'Ejecutar respaldo ahora'}
        </Button>
      </AdminPageHeader>
      <Card>
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2 text-left">Nombre</th>
              <th className="px-3 py-2 text-left">Frecuencia</th>
              <th className="px-3 py-2 text-left">Destino</th>
              <th className="px-3 py-2 text-left">Última ejecución</th>
              <th className="px-3 py-2">Estado</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id} className="border-t">
                <td className="px-3 py-2 font-medium">{r.nombre}</td>
                <td className="px-3 py-2">{r.frecuencia}</td>
                <td className="px-3 py-2 font-mono text-xs">{r.destino_minio_prefix}</td>
                <td className="px-3 py-2 text-xs">{r.ultima_ejecucion || '—'}</td>
                <td className="px-3 py-2">
                  <Badge tone={r.activo ? 'green' : 'slate'}>{r.ultimo_estado || '—'}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </AdminGuard>
  )
}
