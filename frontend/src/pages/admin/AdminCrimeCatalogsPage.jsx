import { useEffect, useState } from 'react'
import { BookOpen, Plus } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Button, Card } from '../../components/ui'
import { useToast } from '../../context/ToastContext'

export default function AdminCrimeCatalogsPage() {
  const toast = useToast()
  const [items, setItems] = useState([])
  const [form, setForm] = useState({
    iucr: '',
    primary_type: '',
    description: '',
    fbi_code: '',
    activo: true,
  })

  const load = () => adminApi.catalogos().then((d) => setItems(d.items || []))
  useEffect(() => {
    load()
  }, [])

  const add = async (e) => {
    e.preventDefault()
    try {
      await adminApi.createCatalogo(form)
      toast.success('Éxito', 'Delito agregado al catálogo')
      setForm({ iucr: '', primary_type: '', description: '', fbi_code: '', activo: true })
      load()
    } catch (err) {
      toast.error('Error', err.message)
    }
  }

  return (
    <AdminGuard>
      <AdminPageHeader
        title="Catálogos de delitos"
        subtitle="IUCR, tipos primarios y códigos FBI"
        icon={BookOpen}
      />
      <Card className="mb-6">
        <form onSubmit={add} className="grid gap-3 sm:grid-cols-5">
          <input
            placeholder="IUCR"
            value={form.iucr}
            onChange={(e) => setForm({ ...form, iucr: e.target.value })}
            className="rounded-xl border px-3 py-2 text-sm"
            required
          />
          <input
            placeholder="Primary type"
            value={form.primary_type}
            onChange={(e) => setForm({ ...form, primary_type: e.target.value })}
            className="rounded-xl border px-3 py-2 text-sm"
            required
          />
          <input
            placeholder="Descripción"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="rounded-xl border px-3 py-2 text-sm"
          />
          <input
            placeholder="FBI code"
            value={form.fbi_code}
            onChange={(e) => setForm({ ...form, fbi_code: e.target.value })}
            className="rounded-xl border px-3 py-2 text-sm"
          />
          <Button type="submit">
            <Plus className="h-4 w-4" />
            Agregar
          </Button>
        </form>
      </Card>
      <Card>
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2 text-left">IUCR</th>
              <th className="px-3 py-2 text-left">Tipo</th>
              <th className="px-3 py-2 text-left">Descripción</th>
              <th className="px-3 py-2 text-left">FBI</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id} className="border-t">
                <td className="px-3 py-2 font-mono">{c.iucr}</td>
                <td className="px-3 py-2">{c.primary_type}</td>
                <td className="px-3 py-2">{c.description}</td>
                <td className="px-3 py-2">{c.fbi_code}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </AdminGuard>
  )
}
