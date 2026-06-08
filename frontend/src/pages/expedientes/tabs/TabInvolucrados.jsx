import { useCallback, useEffect, useState } from 'react'
import { UserPlus } from 'lucide-react'
import { expedientesApi } from '../../../api/expedientes'
import { Button, Card, Badge, Spinner } from '../../../components/ui'
import { useToast } from '../../../context/ToastContext'

const TIPOS = ['Víctima', 'Testigo', 'Sospechoso']

export default function TabInvolucrados({ caseNumber }) {
  const toast = useToast()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({
    tipo_relacion: 'Testigo',
    nombres: '',
    apellidos: '',
    identificacion: '',
    declaracion: '',
  })

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await expedientesApi.involucrados(caseNumber)
      setItems(res.items || [])
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setLoading(false)
    }
  }, [caseNumber, toast])

  useEffect(() => {
    load()
  }, [load])

  const submit = async (e) => {
    e.preventDefault()
    try {
      await expedientesApi.addInvolucrado(caseNumber, form)
      toast.success('Guardado', 'Involucrado agregado al expediente')
      setForm({
        tipo_relacion: 'Testigo',
        nombres: '',
        apellidos: '',
        identificacion: '',
        declaracion: '',
      })
      load()
    } catch (err) {
      toast.error('Error', err.message)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="p-4">
        <h3 className="mb-3 font-semibold text-slate-900">Personas vinculadas</h3>
        {loading ? (
          <Spinner />
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-500">Sin involucrados registrados.</p>
        ) : (
          <ul className="space-y-2">
            {items.map((p) => (
              <li
                key={p.id_relacion}
                className="rounded-xl border border-slate-100 px-3 py-2 text-sm"
              >
                <div className="flex items-center gap-2">
                  <Badge tone="blue">{p.tipo_relacion}</Badge>
                  <span className="font-medium text-slate-900">
                    {p.nombres} {p.apellidos}
                  </span>
                </div>
                <p className="text-xs text-slate-500">ID: {p.identificacion || 'N/D'}</p>
                {p.declaracion && (
                  <p className="mt-1 text-xs text-slate-600">{p.declaracion}</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card className="p-4">
        <h3 className="mb-3 flex items-center gap-2 font-semibold text-slate-900">
          <UserPlus className="h-4 w-4" />
          Agregar involucrado
        </h3>
        <form onSubmit={submit} className="space-y-3">
          <label className="block text-sm">
            Tipo
            <select
              value={form.tipo_relacion}
              onChange={(e) => setForm({ ...form, tipo_relacion: e.target.value })}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2"
            >
              {TIPOS.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <div className="grid grid-cols-2 gap-2">
            <label className="block text-sm">
              Nombres
              <input
                required
                value={form.nombres}
                onChange={(e) => setForm({ ...form, nombres: e.target.value })}
                className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2"
              />
            </label>
            <label className="block text-sm">
              Apellidos
              <input
                required
                value={form.apellidos}
                onChange={(e) => setForm({ ...form, apellidos: e.target.value })}
                className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2"
              />
            </label>
          </div>
          <label className="block text-sm">
            Identificación
            <input
              value={form.identificacion}
              onChange={(e) => setForm({ ...form, identificacion: e.target.value })}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            Declaración / notas
            <textarea
              value={form.declaracion}
              onChange={(e) => setForm({ ...form, declaracion: e.target.value })}
              rows={2}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2"
            />
          </label>
          <Button type="submit">Agregar</Button>
        </form>
      </Card>
    </div>
  )
}
