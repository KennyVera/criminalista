import { useEffect, useState } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import { Plus, Pencil, Trash2, Search, RefreshCw } from 'lucide-react'
import { api } from '../api/client'
import { Button, Card, Spinner, EmptyState, Badge } from '../components/ui'
import RecordModal from '../components/RecordModal'
import ConfirmDialog from '../components/ConfirmDialog'
import { useToast } from '../context/ToastContext'
import { useAuth } from '../context/AuthContext'
import { canAccessDataCrud } from '../utils/roles'

export default function CollectionCrud() {
  const { user } = useAuth()
  const { slug } = useParams()
  const [meta, setMeta] = useState(null)
  const [data, setData] = useState({ items: [], totalItems: 0, totalPages: 1 })
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const toast = useToast()
  const [modal, setModal] = useState({ open: false, record: null })
  const [confirm, setConfirm] = useState({ open: false, record: null })
  const [deleting, setDeleting] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  const perPage = slug === 'crimes_220k' ? 25 : 20
  const expand = undefined

  // Al cambiar de tabla, volver a página 1
  useEffect(() => {
    setPage(1)
    setSearch('')
  }, [slug])

  useEffect(() => {
    if (!slug) return
    let cancelled = false
    setLoading(true)

    const params = { page, per_page: perPage }
    if (search) params.search = search
    if (expand) params.expand = expand

    Promise.all([api.collectionMeta(slug), api.listRecords(slug, params)])
      .then(([m, d]) => {
        if (cancelled) return
        setMeta(m)
        setData(d)
      })
      .catch((err) => {
        if (!cancelled) {
          toast.error('Error', err.message || 'No se pudieron cargar los datos')
          setData({ items: [], totalItems: 0, totalPages: 1 })
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [slug, page, search, perPage, expand, refreshKey])

  const displayFields = (meta?.fields || []).slice(0, 6)
  const cols = displayFields.map((f) => f.name)

  const handleDelete = async () => {
    if (!confirm.record) return
    setDeleting(true)
    try {
      await api.deleteRecord(slug, confirm.record.id)
      toast.success('Éxito', 'Registro eliminado')
      setConfirm({ open: false, record: null })
      setPage(1)
      reload()
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setDeleting(false)
    }
  }

  const reload = () => setRefreshKey((k) => k + 1)

  if (!canAccessDataCrud(user)) {
    return <Navigate to="/" replace />
  }

  return (
    <section className="space-y-4">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">{meta?.label || slug}</h2>
          <p className="text-sm text-slate-500">
            CRUD — crear, leer, actualizar y eliminar (normativa ISO 9241-210)
          </p>
          <span className="mt-2 inline-block">
            <Badge tone="blue">
              {(data.totalItems ?? 0).toLocaleString('es-CO')} registros
            </Badge>
            {meta?.storage && (
              <Badge tone={meta.storage === 'pocketbase' ? 'gray' : 'green'}>
                {meta.storage === 'pocketbase' ? 'PocketBase' : 'MinIO'}
              </Badge>
            )}
          </span>
        </div>
        <Button onClick={() => setModal({ open: true, record: null })}>
          <Plus className="h-4 w-4" /> Nuevo
        </Button>
      </header>

      <Card className="flex flex-wrap gap-3">
        <div className="relative min-w-[200px] flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            placeholder="Buscar…"
            aria-label="Buscar registros"
            className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-3 text-sm"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
          />
        </div>
        <Button variant="secondary" onClick={reload} aria-label="Recargar">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </Card>

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : data.items?.length === 0 && (data.totalItems ?? 0) === 0 ? (
        <Card>
          <EmptyState
            title="Sin registros"
            description={
              meta?.storage === 'pocketbase'
                ? 'Carga crimes_220k: migrate_from_postgres --steps raw'
                : 'Ejecuta el ETL: python manage.py etl_pb_to_minio'
            }
          />
        </Card>
      ) : data.items?.length === 0 ? (
        <Card>
          <EmptyState
            title="Página sin resultados"
            description="Prueba ir a la página 1 o limpiar la búsqueda."
          />
          <Button className="mx-auto mt-2 block" variant="secondary" onClick={() => setPage(1)}>
            Ir a página 1
          </Button>
        </Card>
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                {cols.map((c) => (
                  <th key={c} className="px-4 py-3 font-semibold">
                    {c}
                  </th>
                ))}
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((row) => (
                <tr key={row.id} className="border-t border-slate-100 hover:bg-slate-50/50">
                  {cols.map((c) => (
                    <td key={c} className="max-w-[180px] truncate px-4 py-3 text-slate-700">
                      {String(
                        row[c] !== undefined && row[c] !== null && row[c] !== ''
                          ? row[c]
                          : row.expand?.[c]?.primary_type ??
                            row.expand?.[c]?.district ??
                            '—'
                      ).slice(0, 80)}
                    </td>
                  ))}
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      className="rounded-lg p-2 text-slate-500 hover:bg-brand-50 hover:text-brand-600"
                      onClick={() => setModal({ open: true, record: row })}
                      aria-label="Editar"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      className="rounded-lg p-2 text-slate-500 hover:bg-red-50 hover:text-red-600"
                      onClick={() => setConfirm({ open: true, record: row })}
                      aria-label="Eliminar"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {!loading && (data.totalItems ?? 0) > 0 && (
        <nav className="flex items-center justify-between text-sm" aria-label="Paginación">
          <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Anterior
          </Button>
          <span className="text-slate-600">
            Página {page} de {data.totalPages || 1}
          </span>
          <Button
            variant="secondary"
            disabled={page >= (data.totalPages || 1)}
            onClick={() => setPage((p) => p + 1)}
          >
            Siguiente
          </Button>
        </nav>
      )}

      <RecordModal
        open={modal.open}
        record={modal.record}
        meta={meta}
        onClose={() => setModal({ open: false, record: null })}
        onSaved={() => setPage(1)}
      />
      <ConfirmDialog
        open={confirm.open}
        title="¿Eliminar registro?"
        message="Esta acción no se puede deshacer."
        onCancel={() => setConfirm({ open: false, record: null })}
        onConfirm={handleDelete}
        loading={deleting}
      />
    </section>
  )
}
