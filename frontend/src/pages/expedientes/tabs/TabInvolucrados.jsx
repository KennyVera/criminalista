import { useCallback, useEffect, useState } from 'react'
import { UserPlus, Users } from 'lucide-react'
import { expedientesApi } from '../../../api/expedientes'
import { Button, Card, Badge, Spinner } from '../../../components/ui'
import { useToast } from '../../../context/ToastContext'

const TIPOS = ['Víctima', 'Testigo', 'Sospechoso']

const TIPO_TONE = {
  Víctima: 'red',
  Testigo: 'blue',
  Sospechoso: 'gray',
}

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
      <Card className="glass-card p-5">
        <div className="mb-4 flex items-center gap-2">
          <Users className="h-5 w-5 text-indigo-600" />
          <h3 className="font-semibold text-slate-900">Personas vinculadas</h3>
        </div>
        {loading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : items.length === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 px-4 py-8 text-center text-sm text-slate-500">
            No hay personas registradas en este expediente.
          </p>
        ) : (
          <ul className="space-y-2.5">
            {items.map((p) => (
              <li
                key={p.id_relacion}
                className="rounded-xl border border-slate-200/70 bg-white/60 px-4 py-3 text-sm shadow-sm transition hover:border-indigo-200 hover:shadow-md"
              >
                <div className="flex items-center gap-2">
                  <Badge tone={TIPO_TONE[p.tipo_relacion] || 'blue'}>{p.tipo_relacion}</Badge>
                  <span className="font-semibold text-slate-900">
                    {p.nombres} {p.apellidos}
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  Identificación: {p.identificacion || 'No registrada'}
                </p>
                {p.declaracion && (
                  <p className="mt-2 rounded-lg bg-slate-50/80 px-2.5 py-1.5 text-xs leading-relaxed text-slate-600">
                    {p.declaracion}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card className="glass-card p-5">
        <h3 className="mb-4 flex items-center gap-2 font-semibold text-slate-900">
          <UserPlus className="h-5 w-5 text-indigo-600" />
          Agregar involucrado
        </h3>
        <form onSubmit={submit} className="space-y-3">
          <label className="block text-sm font-medium text-slate-700">
            Tipo de relación
            <select
              value={form.tipo_relacion}
              onChange={(e) => setForm({ ...form, tipo_relacion: e.target.value })}
              className="input-field mt-1.5"
            >
              {TIPOS.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block text-sm font-medium text-slate-700">
              Nombres
              <input
                required
                value={form.nombres}
                onChange={(e) => setForm({ ...form, nombres: e.target.value })}
                className="input-field mt-1.5"
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Apellidos
              <input
                required
                value={form.apellidos}
                onChange={(e) => setForm({ ...form, apellidos: e.target.value })}
                className="input-field mt-1.5"
              />
            </label>
          </div>
          <label className="block text-sm font-medium text-slate-700">
            Identificación
            <input
              value={form.identificacion}
              onChange={(e) => setForm({ ...form, identificacion: e.target.value })}
              placeholder="Cédula, pasaporte u otro documento"
              className="input-field mt-1.5"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Declaración / notas
            <textarea
              value={form.declaracion}
              onChange={(e) => setForm({ ...form, declaracion: e.target.value })}
              rows={2}
              placeholder="Resumen de la declaración o notas relevantes…"
              className="input-field mt-1.5"
            />
          </label>
          <Button type="submit">Agregar involucrado</Button>
        </form>
      </Card>
    </div>
  )
}
