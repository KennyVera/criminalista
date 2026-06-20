import { useEffect, useState } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import { Plus, Pencil, Trash2, Search, RefreshCw, Database } from 'lucide-react'
import { api } from '../api/client'
import { Button, Card, Spinner, EmptyState, Badge } from '../components/ui'
import PageHeader from '../components/layout/PageHeader'
import TablePagination from '../components/layout/TablePagination'
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
    <section className="space-y-6">
      <PageHeader
        title={meta?.label || slug}
        subtitle="Gestión de registros — crear, consultar, actualizar y eliminar"
        icon={Database}
        badge={
          <div className="flex flex-wrap gap-2">
            <Badge tone="info">
              {(data.totalItems ?? 0).toLocaleString('es-CO')} registros
            </Badge>
            {meta?.storage && (
              <Badge tone={meta.storage === 'pocketbase' ? 'neutral' : 'active'}>
                {meta.storage === 'pocketbase' ? 'PocketBase' : 'MinIO'}
              </Badge>
            )}
          </div>
        }
        actions={
          <Button onClick={() => setModal({ open: true, record: null })}>
            <Plus className="h-4 w-4" /> Nuevo registro
          </Button>
        }
      />

      <Card className="flex flex-wrap items-center gap-3 p-4">
        <div className="relative min-w-[200px] flex-1">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            placeholder="Buscar en la tabla…"
            aria-label="Buscar registros"
            className="search-field"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
          />
        </div>
        <Button variant="secondary" onClick={reload} aria-label="Recargar">
          <RefreshCw className="h-4 w-4" />
          <span className="hidden sm:inline">Actualizar</span>
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
        <Card flush className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  {cols.map((c) => (
                    <th key={c}>{c}</th>
                  ))}
                  <th className="text-right">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((row) => (
                  <tr key={row.id}>
                    {cols.map((c) => (
                      <td key={c} className="max-w-[180px] truncate text-slate-700 dark:text-slate-300">
                        {String(
                          row[c] !== undefined && row[c] !== null && row[c] !== ''
                            ? row[c]
                            : row.expand?.[c]?.primary_type ??
                              row.expand?.[c]?.district ??
                              '—'
                        ).slice(0, 80)}
                      </td>
                    ))}
                    <td className="text-right">
                      <div className="inline-flex gap-1">
                        <button
                          type="button"
                          className="rounded-lg p-2 text-slate-500 transition hover:bg-indigo-50 hover:text-indigo-600 dark:hover:bg-indigo-950/50"
                          onClick={() => setModal({ open: true, record: row })}
                          aria-label="Editar"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          className="rounded-lg p-2 text-slate-500 transition hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/50"
                          onClick={() => setConfirm({ open: true, record: row })}
                          aria-label="Eliminar"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <TablePagination
            page={page}
            totalPages={data.totalPages || 1}
            totalItems={data.totalItems ?? 0}
            perPage={perPage}
            onPageChange={setPage}
            itemLabel="registros"
          />
        </Card>
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
