# Generates frontend components (run once)
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "src"

def w(rel: str, content: str):
    p = BASE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.replace("motion", "div"), encoding="utf-8")
    print("ok", rel)

w("components/RecordModal.jsx", '''
import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { Button } from './ui'
import { api } from '../api/client'

export default function RecordModal({ open, onClose, meta, record, onSaved }) {
  const [form, setForm] = useState({})
  const [relations, setRelations] = useState({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const isEdit = Boolean(record?.id)
  const fields = meta?.fields || []
  const rels = meta?.relations || []

  useEffect(() => {
    if (!open) return
    setError(null)
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
    setError(null)
    const body = { ...form }
    Object.keys(body).forEach((k) => {
      if (body[k] === '') delete body[k]
    })
    try {
      if (isEdit) {
        await api.updateRecord(meta.slug, record.id, body)
      } else {
        await api.createRecord(meta.slug, body)
      }
      onSaved()
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm" role="dialog" aria-modal="true">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
        <motion className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">
            {isEdit ? 'Editar registro' : 'Nuevo registro'}
          </h2>
          <button type="button" onClick={onClose} className="rounded-lg p-2 hover:bg-slate-100" aria-label="Cerrar">
            <X className="h-5 w-5" />
          </button>
        </motion>
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
          {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
          <motion className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
            <Button type="submit" disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</Button>
          </motion>
        </form>
      </motion>
    </motion>
  )
}
''')

w("components/ConfirmDialog.jsx", '''
import { Button } from './ui'

export default function ConfirmDialog({ open, title, message, onConfirm, onCancel, loading }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" role="alertdialog" aria-modal="true">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        <p className="mt-2 text-sm text-slate-600">{message}</p>
        <motion className="mt-6 flex justify-end gap-2">
          <Button variant="secondary" onClick={onCancel}>Cancelar</Button>
          <Button variant="danger" onClick={onConfirm} disabled={loading}>
            {loading ? 'Eliminando…' : 'Eliminar'}
          </Button>
        </motion>
      </motion>
    </motion>
  )
}
''')

w("pages/CollectionCrud.jsx", '''
import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Plus, Pencil, Trash2, Search, RefreshCw } from 'lucide-react'
import { api } from '../api/client'
import { Button, Card, Spinner, EmptyState, Badge } from '../components/ui'
import RecordModal from '../components/RecordModal'
import ConfirmDialog from '../components/ConfirmDialog'

export default function CollectionCrud() {
  const { slug } = useParams()
  const [meta, setMeta] = useState(null)
  const [data, setData] = useState({ items: [], totalItems: 0, totalPages: 1 })
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState({ open: false, record: null })
  const [confirm, setConfirm] = useState({ open: false, record: null })
  const [deleting, setDeleting] = useState(false)

  const perPage = slug === 'crimes_220k' ? 25 : 20
  const expand = slug === 'fact_crimes'
    ? 'caso,tipo_crimen,distrito,tiempo,ubicacion_geo'
    : undefined

  const load = useCallback(() => {
    setLoading(true)
    Promise.all([
      api.collectionMeta(slug),
      api.listRecords(slug, {
        page,
        per_page: perPage,
        search: search || undefined,
        expand,
      }),
    ])
      .then(([m, d]) => {
        setMeta(m)
        setData(d)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [slug, page, search, perPage, expand])

  useEffect(() => {
    setPage(1)
  }, [slug, search])

  useEffect(() => {
    load()
  }, [load])

  const displayFields = (meta?.fields || []).slice(0, 6)
  const cols = displayFields.map((f) => f.name)

  const handleDelete = async () => {
    if (!confirm.record) return
    setDeleting(true)
    try {
      await api.deleteRecord(slug, confirm.record.id)
      setConfirm({ open: false, record: null })
      load()
    } catch (e) {
      alert(e.message)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <section className="space-y-4">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <motion>
          <h2 className="text-xl font-bold text-slate-900">{meta?.label || slug}</h2>
          <p className="text-sm text-slate-500">
            CRUD — crear, leer, actualizar y eliminar (normativa ISO 9241-210)
          </p>
          <Badge tone="blue" className="mt-2">{data.totalItems?.toLocaleString?.('es-CO')} registros</Badge>
        </motion>
        <Button onClick={() => setModal({ open: true, record: null })}>
          <Plus className="h-4 w-4" /> Nuevo
        </Button>
      </header>

      <Card className="flex flex-wrap gap-3">
        <motion className="relative min-w-[200px] flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            placeholder="Buscar…"
            aria-label="Buscar registros"
            className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-3 text-sm"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </motion>
        <Button variant="secondary" onClick={load} aria-label="Recargar">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </Card>

      {loading ? (
        <motion className="flex justify-center py-16"><Spinner /></motion>
      ) : data.items?.length === 0 ? (
        <Card>
          <EmptyState title="Sin registros" description="Crea el primero con el botón Nuevo." />
        </Card>
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                {cols.map((c) => (
                  <th key={c} className="px-4 py-3 font-semibold">{c}</th>
                ))}
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((row) => (
                <tr key={row.id} className="border-t border-slate-100 hover:bg-slate-50/50">
                  {cols.map((c) => (
                    <td key={c} className="max-w-[180px] truncate px-4 py-3 text-slate-700">
                      {String(row[c] ?? row.expand?.[c]?.primary_type ?? row.expand?.[c]?.district ?? '—').slice(0, 80)}
                    </td>
                  ))}
                  <td className="px-4 py-3 text-right">
                    <button type="button" className="rounded-lg p-2 text-slate-500 hover:bg-brand-50 hover:text-brand-600" onClick={() => setModal({ open: true, record: row })} aria-label="Editar">
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button type="button" className="rounded-lg p-2 text-slate-500 hover:bg-red-50 hover:text-red-600" onClick={() => setConfirm({ open: true, record: row })} aria-label="Eliminar">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      <nav className="flex items-center justify-between text-sm" aria-label="Paginación">
        <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Anterior</Button>
        <span className="text-slate-600">Página {page} de {data.totalPages || 1}</span>
        <Button variant="secondary" disabled={page >= (data.totalPages || 1)} onClick={() => setPage((p) => p + 1)}>Siguiente</Button>
      </nav>

      <RecordModal
        open={modal.open}
        record={modal.record}
        meta={meta}
        onClose={() => setModal({ open: false, record: null })}
        onSaved={load}
      />
      <ConfirmDialog
        open={confirm.open}
        title="¿Eliminar registro?"
        message="Esta acción no se puede deshacer. Confirma para eliminar el registro de PocketBase."
        onCancel={() => setConfirm({ open: false, record: null })}
        onConfirm={handleDelete}
        loading={deleting}
      />
    </section>
  )
}
''')

w("App.jsx", '''
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import DashboardLayout from './layouts/DashboardLayout'
import Dashboard from './pages/Dashboard'
import CollectionCrud from './pages/CollectionCrud'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="tabla/:slug" element={<CollectionCrud />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
''')

w("main.jsx", '''
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
''')

for p in BASE.rglob("*.jsx"):
    t = p.read_text(encoding="utf-8")
    if "motion" in t:
        p.write_text(t.replace("motion", "div"), encoding="utf-8")
        print("fixed", p.name)