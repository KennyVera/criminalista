import { useEffect, useState } from 'react'
import { MapPin, Plus } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Button, Card } from '../../components/ui'
import { useToast } from '../../context/ToastContext'

export default function AdminZonesPage() {
  const toast = useToast()
  const [items, setItems] = useState([])
  const [form, setForm] = useState({
    nombre: '',
    tipo_zona: 'Operativa',
    distrito: '',
    comunidad: '',
    lat_centro: '',
    lon_centro: '',
    activa: true,
  })

  const load = () => adminApi.zonas().then((d) => setItems(d.items || []))
  useEffect(() => {
    load()
  }, [])

  const add = async (e) => {
    e.preventDefault()
    try {
      await adminApi.createZona(form)
      toast.success('Éxito', 'Zona geográfica registrada')
      setForm({
        nombre: '',
        tipo_zona: 'Operativa',
        distrito: '',
        comunidad: '',
        lat_centro: '',
        lon_centro: '',
        activa: true,
      })
      load()
    } catch (err) {
      toast.error('Error', err.message)
    }
  }

  return (
    <AdminGuard>
      <AdminPageHeader
        title="Zonas geográficas"
        subtitle="Áreas operativas y distritos CPD"
        icon={MapPin}
      />
      <Card className="mb-6">
        <form onSubmit={add} className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {['nombre', 'tipo_zona', 'distrito', 'comunidad', 'lat_centro', 'lon_centro'].map(
            (field) => (
              <input
                key={field}
                placeholder={field}
                value={form[field]}
                onChange={(e) => setForm({ ...form, [field]: e.target.value })}
                className="rounded-xl border px-3 py-2 text-sm"
                required={field === 'nombre'}
              />
            )
          )}
          <Button type="submit" className="sm:col-span-3 lg:col-span-6">
            <Plus className="h-4 w-4" />
            Agregar zona
          </Button>
        </form>
      </Card>
      <Card>
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2 text-left">Nombre</th>
              <th className="px-3 py-2 text-left">Tipo</th>
              <th className="px-3 py-2 text-left">Distrito</th>
              <th className="px-3 py-2 text-left">Comunidad</th>
              <th className="px-3 py-2 text-left">Coordenadas</th>
            </tr>
          </thead>
          <tbody>
            {items.map((z) => (
              <tr key={z.id} className="border-t">
                <td className="px-3 py-2 font-medium">{z.nombre}</td>
                <td className="px-3 py-2">{z.tipo_zona}</td>
                <td className="px-3 py-2">{z.distrito}</td>
                <td className="px-3 py-2">{z.comunidad}</td>
                <td className="px-3 py-2 text-xs">
                  {z.lat_centro}, {z.lon_centro}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </AdminGuard>
  )
}
