import { useEffect, useState } from 'react'
import { MapPin, Plus } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Button, Card, Badge } from '../../components/ui'
import { useToast } from '../../context/ToastContext'

const INPUT =
  'rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 transition focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-100'

const FIELD_LABELS = {
  nombre: 'Nombre',
  tipo_zona: 'Tipo de zona',
  distrito: 'Distrito',
  comunidad: 'Comunidad',
  lat_centro: 'Latitud',
  lon_centro: 'Longitud',
}

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
      <Card className="mb-6 border-brand-200/40 bg-gradient-to-br from-brand-50/30 to-white">
        <p className="mb-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Nueva zona
        </p>
        <form onSubmit={add} className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {['nombre', 'tipo_zona', 'distrito', 'comunidad', 'lat_centro', 'lon_centro'].map(
            (field) => (
              <input
                key={field}
                placeholder={FIELD_LABELS[field] || field}
                value={form[field]}
                onChange={(e) => setForm({ ...form, [field]: e.target.value })}
                className={INPUT}
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
      <Card className="overflow-hidden p-0">
        <div className="border-b border-slate-100 bg-slate-50/80 px-5 py-3">
          <p className="text-sm font-semibold text-slate-900">
            {items.length} zona{items.length !== 1 ? 's' : ''} registrada{items.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-200 bg-slate-50/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Nombre
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Tipo
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Distrito
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Comunidad
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Coordenadas
                </th>
              </tr>
            </thead>
            <tbody>
              {items.map((z) => (
                <tr
                  key={z.id}
                  className="border-b border-slate-100 transition hover:bg-slate-50/60"
                >
                  <td className="px-4 py-3 font-medium text-slate-900">{z.nombre}</td>
                  <td className="px-4 py-3">
                    <Badge tone="blue">{z.tipo_zona}</Badge>
                  </td>
                  <td className="px-4 py-3 text-slate-700">{z.distrito}</td>
                  <td className="px-4 py-3 text-slate-700">{z.comunidad}</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">
                    {z.lat_centro}, {z.lon_centro}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </AdminGuard>
  )
}
