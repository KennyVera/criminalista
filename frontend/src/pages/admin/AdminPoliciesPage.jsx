import { useEffect, useState } from 'react'
import { Shield } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Card, Badge } from '../../components/ui'
import { useToast } from '../../context/ToastContext'

export default function AdminPoliciesPage() {
  const [items, setItems] = useState([])
  const toast = useToast()

  const load = () => adminApi.politicas().then((d) => setItems(d.items || []))
  useEffect(() => {
    load()
  }, [])

  const toggle = async (row) => {
    try {
      await adminApi.updatePolitica(row.id_politica, { activa: !row.activa })
      toast.success('Éxito', 'Política actualizada')
      load()
    } catch (e) {
      toast.error('Error', e.message)
    }
  }

  return (
    <AdminGuard>
      <AdminPageHeader
        title="Políticas de seguridad"
        subtitle="Parámetros de seguridad del sistema (incluye gestión de permisos)"
        icon={Shield}
      />
      <Card>
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2 text-left">Política</th>
              <th className="px-3 py-2 text-left">Clave</th>
              <th className="px-3 py-2 text-left">Valor</th>
              <th className="px-3 py-2">Estado</th>
            </tr>
          </thead>
          <tbody>
            {items.map((p) => (
              <tr key={p.id_politica} className="border-t">
                <td className="px-3 py-2 font-medium">{p.nombre}</td>
                <td className="px-3 py-2 font-mono text-xs">{p.clave}</td>
                <td className="px-3 py-2">{p.valor}</td>
                <td className="px-3 py-2">
                  <button type="button" onClick={() => toggle(p)}>
                    <Badge tone={p.activa ? 'green' : 'slate'}>
                      {p.activa ? 'Activa' : 'Inactiva'}
                    </Badge>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </AdminGuard>
  )
}
