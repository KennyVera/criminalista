import { useEffect, useState } from 'react'
import { BookOpen, Plus } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Button, Card } from '../../components/ui'
import { useToast } from '../../context/ToastContext'

const INPUT =
  'rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 transition focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-100'

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
      <Card className="mb-6 border-brand-200/40 bg-gradient-to-br from-brand-50/30 to-white">
        <p className="mb-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Nuevo delito
        </p>
        <form onSubmit={add} className="grid gap-3 sm:grid-cols-5">
          <input
            placeholder="IUCR"
            value={form.iucr}
            onChange={(e) => setForm({ ...form, iucr: e.target.value })}
            className={INPUT}
            required
          />
          <input
            placeholder="Primary type"
            value={form.primary_type}
            onChange={(e) => setForm({ ...form, primary_type: e.target.value })}
            className={INPUT}
            required
          />
          <input
            placeholder="Descripción"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className={INPUT}
          />
          <input
            placeholder="FBI code"
            value={form.fbi_code}
            onChange={(e) => setForm({ ...form, fbi_code: e.target.value })}
            className={INPUT}
          />
          <Button type="submit">
            <Plus className="h-4 w-4" />
            Agregar
          </Button>
        </form>
      </Card>
      <Card className="overflow-hidden p-0">
        <div className="border-b border-slate-100 bg-slate-50/80 px-5 py-3">
          <p className="text-sm font-semibold text-slate-900">
            {items.length} registro{items.length !== 1 ? 's' : ''} en catálogo
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-200 bg-slate-50/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  IUCR
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Tipo
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Descripción
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  FBI
                </th>
              </tr>
            </thead>
            <tbody>
              {items.map((c) => (
                <tr
                  key={c.id}
                  className="border-b border-slate-100 transition hover:bg-slate-50/60"
                >
                  <td className="px-4 py-3 font-mono text-xs font-medium text-brand-700">{c.iucr}</td>
                  <td className="px-4 py-3 text-slate-800">{c.primary_type}</td>
                  <td className="px-4 py-3 text-slate-600">{c.description}</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">{c.fbi_code}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </AdminGuard>
  )
}
