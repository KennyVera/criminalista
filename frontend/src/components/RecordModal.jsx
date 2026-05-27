
import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { Button } from './ui'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'

export default function RecordModal({ open, onClose, meta, record, onSaved }) {
  const [form, setForm] = useState({})
  const [relations, setRelations] = useState({})
  const [saving, setSaving] = useState(false)
  const toast = useToast()

  const isEdit = Boolean(record?.id)
  const fields = meta?.fields || []
  const rels = meta?.relations || []

  useEffect(() => {
    if (!open) return
    const initial = {}
    fields.forEach((f) => {
      initial[f.name] = record?.[f.name] ?? (f.type === 'bool' ? false : '')
    })
    rels.forEach((r) => {
      initial[r.name] = record?.[r.name] || ''
    })
    setForm(initial)
    rels.forEach(async (r) => {
      try {
        const data = await api.relationOptions(r.collection)
        setRelations((prev) => ({ ...prev, [r.name]: data.options || [] }))
      } catch {
        setRelations((prev) => ({ ...prev, [r.name]: [] }))
      }
    })
  }, [open, record, meta])

  if (!open) return null

  const handleChange = (name, value, type) => {
    let v = value
    if (type === 'bool') v = value === 'true' || value === true
    if (type === 'number' && value !== '') v = Number(value)
    setForm((f) => ({ ...f, [name]: v }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    const body = { ...form }
    Object.keys(body).forEach((k) => {
      if (body[k] === '') delete body[k]
    })
    try {
      if (isEdit) {
        await api.updateRecord(meta.slug, record.id, body)
        toast.success('Éxito', 'Registro actualizado correctamente')
      } else {
        await api.createRecord(meta.slug, body)
        toast.success('Éxito', 'Registro creado correctamente')
      }
      onSaved()
      onClose()
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm" role="dialog" aria-modal="true">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">
            {isEdit ? 'Editar registro' : 'Nuevo registro'}
          </h2>
          <button type="button" onClick={onClose} className="rounded-lg p-2 hover:bg-slate-100" aria-label="Cerrar">
            <X className="h-5 w-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {fields.map((f) => (
            <label key={f.name} className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">{f.label}</span>
              {f.type === 'bool' ? (
                <select
                  className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  value={String(form[f.name])}
                  onChange={(e) => handleChange(f.name, e.target.value, 'bool')}
                >
                  <option value="false">No</option>
                  <option value="true">Sí</option>
                </select>
              ) : (
                <input
                  type={f.type === 'number' ? 'number' : f.type === 'date' ? 'datetime-local' : 'text'}
                  className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
                  value={form[f.name] ?? ''}
                  onChange={(e) => handleChange(f.name, e.target.value, f.type)}
                />
              )}
            </label>
          ))}
          {rels.map((r) => (
            <label key={r.name} className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">{r.label}</span>
              <select
                className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                value={form[r.name] || ''}
                onChange={(e) => setForm((f) => ({ ...f, [r.name]: e.target.value }))}
              >
                <option value="">— Sin enlace —</option>
                {(relations[r.name] || []).map((o) => (
                  <option key={o.id} value={o.id}>{o.label}</option>
                ))}
              </select>
            </label>
          ))}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
            <Button type="submit" disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</Button>
          </div>
        </form>
      </div>
    </div>
  )
}
