import { useCallback, useEffect, useState } from 'react'
import {
  HardDrive,
  Plus,
  Play,
  Pencil,
  History,
  Download,
  Upload,
  Trash2,
} from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import ConfirmDialog from '../../components/ConfirmDialog'
import { adminApi } from '../../api/admin'
import RestoreProgressCard from '../../components/RestoreProgressCard'
import { Button, Card, Badge, Spinner } from '../../components/ui'
import { useToast } from '../../context/ToastContext'
import { useRestoreWithEtl } from '../../hooks/useRestoreWithEtl'

const FRECUENCIAS = [
  { value: 'horario', label: 'Horario (cada 24 h)' },
  { value: 'diario', label: 'Diario' },
  { value: 'semanal', label: 'Semanal' },
  { value: 'mensual', label: 'Mensual' },
]

const TIPOS = [
  { value: 'completo', label: 'Completo (todas las tablas transaccionales)' },
  { value: 'incremental', label: 'Incremental (sesiones y auditoría)' },
]

const emptyConfig = {
  nombre: '',
  frecuencia: 'diario',
  destino_minio_prefix: 'backups/daily',
  tipo_respaldo: 'completo',
  hora_programada: '02:00',
  activo: true,
}

function estadoTone(estado) {
  const e = String(estado || '').toLowerCase()
  if (e === 'completado') return 'green'
  if (e === 'fallido' || e === 'error') return 'red'
  if (e === 'en_progreso') return 'blue'
  return 'slate'
}

function formatDt(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('es-CO')
  } catch {
    return iso
  }
}

function canDeleteHistorial(h) {
  return String(h?.estado || '').toLowerCase() !== 'en_progreso'
}

export default function AdminBackupsPage() {
  const [items, setItems] = useState([])
  const [historial, setHistorial] = useState([])
  const [runningId, setRunningId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(emptyConfig)
  const [restoreFile, setRestoreFile] = useState(null)
  const [selectedHist, setSelectedHist] = useState(() => new Set())
  const [deleteDialog, setDeleteDialog] = useState(null)
  const [deletingHist, setDeletingHist] = useState(false)
  const toast = useToast()
  const {
    run: runRestoreWithEtl,
    running: restoring,
    progress: restoreProgress,
    cancel: cancelRestore,
    canCancel,
  } = useRestoreWithEtl({
    startRestore: adminApi.restoreRespaldoZip,
    getStatus: adminApi.restoreRespaldoStatus,
    cancelRestore: adminApi.cancelRestoreRespaldo,
  })

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [cfg, hist] = await Promise.all([
        adminApi.respaldos(false),
        adminApi.respaldosHistorial(100),
      ])
      setItems(cfg.items || [])
      setHistorial(hist.items || [])
      setSelectedHist(new Set())
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    load()
  }, [load])

  const openCreate = () => {
    setEditing(null)
    setForm(emptyConfig)
    setFormOpen(true)
  }

  const openEdit = (row) => {
    setEditing(row)
    setForm({
      nombre: row.nombre || '',
      frecuencia: row.frecuencia || 'diario',
      destino_minio_prefix: row.destino_minio_prefix || 'backups/daily',
      tipo_respaldo: row.tipo_respaldo || 'completo',
      hora_programada: row.hora_programada || '02:00',
      activo: Boolean(row.activo),
    })
    setFormOpen(true)
  }

  const saveConfig = async (e) => {
    e.preventDefault()
    try {
      if (editing) {
        await adminApi.updateRespaldo(editing.id, form)
        toast.success('Éxito', 'Configuración actualizada')
      } else {
        await adminApi.createRespaldoConfig(form)
        toast.success('Éxito', 'Respaldo programado creado')
      }
      setFormOpen(false)
      load()
    } catch (err) {
      toast.error('Error', err.message)
    }
  }

  const descargar = async (historialId) => {
    try {
      await adminApi.downloadRespaldo(historialId)
      toast.success('Éxito', 'ZIP descargado en tu equipo')
    } catch (e) {
      toast.error('Error', e.message)
    }
  }

  const deletableHistorial = historial.filter(canDeleteHistorial)
  const allDeletableSelected =
    deletableHistorial.length > 0 &&
    deletableHistorial.every((h) => selectedHist.has(h.id))

  const toggleHistSelect = (id) => {
    setSelectedHist((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleSelectAllHist = () => {
    if (allDeletableSelected) {
      setSelectedHist(new Set())
    } else {
      setSelectedHist(new Set(deletableHistorial.map((h) => h.id)))
    }
  }

  const confirmDeleteHistorial = (ids, label) => {
    setDeleteDialog({ ids, label })
  }

  const runDeleteHistorial = async () => {
    if (!deleteDialog?.ids?.length) return
    setDeletingHist(true)
    try {
      const ids = deleteDialog.ids
      if (ids.length === 1) {
        await adminApi.deleteRespaldoHistorial(ids[0])
        toast.success('Eliminado', 'Registro y archivos en MinIO eliminados')
      } else {
        const r = await adminApi.deleteRespaldoHistorialBulk(ids)
        const n = r.deleted_count ?? r.deleted?.length ?? 0
        if (r.errors?.length) {
          toast.warning(
            'Parcial',
            `Eliminados ${n}. ${r.errors.length} no se pudieron borrar.`
          )
        } else {
          toast.success('Eliminados', `${n} registro(s) del historial`)
        }
      }
      setDeleteDialog(null)
      setSelectedHist(new Set())
      load()
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setDeletingHist(false)
    }
  }

  const restaurarZip = async () => {
    if (!restoreFile) {
      toast.warning('Atención', 'Selecciona un archivo ZIP de respaldo')
      return
    }
    try {
      const r = await runRestoreWithEtl(restoreFile)
      if (r?.cancelled) {
        toast.info('Cancelado', r?.message || 'Se restauró el estado anterior en MinIO.')
        return
      }
      const tx = r?.restore?.restored_transaccional || []
      const adm = r?.restore?.restored_administracion || []
      toast.success(
        'Restauración + ETL',
        r?.message || `Completado. Tablas TX: ${tx.length}, Admin: ${adm.length}`
      )
      setRestoreFile(null)
      load()
    } catch (e) {
      toast.error('Error', e.message)
    }
  }

  const ejecutar = async (id) => {
    setRunningId(id)
    try {
      const r = await adminApi.runRespaldo(id)
      if (r.success) {
        toast.success('Éxito', r.detalle || `Respaldo OK (${r.tablas_copiadas} tablas)`)
      } else {
        toast.error('Respaldo fallido', r.detalle || 'No se completó correctamente')
      }
      load()
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setRunningId(null)
    }
  }

  return (
    <AdminGuard>
      <AdminPageHeader
        title="Configurar respaldos"
        subtitle="CU-17 — Programación, ejecución manual e historial (MinIO)"
        icon={HardDrive}
      >
        <Button type="button" onClick={openCreate}>
          <Plus className="h-4 w-4" />
          Nueva programación
        </Button>
      </AdminPageHeader>

      <p className="mb-4 text-sm text-slate-600">
        El respaldo <strong>completo</strong> guarda las 7 tablas transaccionales + 8 tablas de
        administración en MinIO y en el ZIP descargable. Al restaurar desde ZIP se ejecuta
        automáticamente el ETL del modelo estrella (hechos y dimensiones para el dashboard).
      </p>

      {formOpen && (
        <Card className="mb-6 border-brand-200 p-6">
          <form onSubmit={saveConfig} className="space-y-4">
            <h3 className="font-semibold text-slate-900">
              {editing ? 'Editar programación' : 'Nueva programación de respaldo'}
            </h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block sm:col-span-2">
                <span className="mb-1 block text-xs font-medium text-slate-600">Nombre</span>
                <input
                  value={form.nombre}
                  onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                  className="w-full rounded-xl border px-3 py-2 text-sm"
                  required
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-medium text-slate-600">Frecuencia</span>
                <select
                  value={form.frecuencia}
                  onChange={(e) => setForm({ ...form, frecuencia: e.target.value })}
                  className="w-full rounded-xl border px-3 py-2 text-sm"
                >
                  {FRECUENCIAS.map((f) => (
                    <option key={f.value} value={f.value}>
                      {f.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-medium text-slate-600">
                  Hora programada
                </span>
                <input
                  type="time"
                  value={form.hora_programada}
                  onChange={(e) => setForm({ ...form, hora_programada: e.target.value })}
                  className="w-full rounded-xl border px-3 py-2 text-sm"
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-medium text-slate-600">
                  Tipo de respaldo
                </span>
                <select
                  value={form.tipo_respaldo}
                  onChange={(e) => setForm({ ...form, tipo_respaldo: e.target.value })}
                  className="w-full rounded-xl border px-3 py-2 text-sm"
                >
                  {TIPOS.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-medium text-slate-600">
                  Destino MinIO (prefijo)
                </span>
                <input
                  value={form.destino_minio_prefix}
                  onChange={(e) =>
                    setForm({ ...form, destino_minio_prefix: e.target.value })
                  }
                  className="w-full rounded-xl border px-3 py-2 font-mono text-sm"
                  required
                />
              </label>
              <label className="flex items-center gap-2 sm:col-span-2">
                <input
                  type="checkbox"
                  checked={form.activo}
                  onChange={(e) => setForm({ ...form, activo: e.target.checked })}
                />
                <span className="text-sm text-slate-700">Programación activa</span>
              </label>
            </div>
            <div className="flex gap-2">
              <Button type="submit">Guardar</Button>
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>
                Cancelar
              </Button>
            </div>
          </form>
        </Card>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : (
        <>
          <Card className="mb-6 overflow-x-auto">
            <h3 className="border-b px-4 py-3 font-semibold text-slate-900">
              Programaciones activas
            </h3>
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-3 py-2 text-left">Nombre</th>
                  <th className="px-3 py-2 text-left">Frecuencia</th>
                  <th className="px-3 py-2 text-left">Tipo</th>
                  <th className="px-3 py-2 text-left">Destino</th>
                  <th className="px-3 py-2 text-left">Próxima</th>
                  <th className="px-3 py-2 text-left">Última</th>
                  <th className="px-3 py-2">Estado</th>
                  <th className="px-3 py-2">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {items.map((r) => (
                  <tr key={r.id} className="border-t">
                    <td className="px-3 py-2 font-medium">{r.nombre}</td>
                    <td className="px-3 py-2">{r.frecuencia}</td>
                    <td className="px-3 py-2 capitalize">{r.tipo_respaldo || 'completo'}</td>
                    <td className="px-3 py-2 font-mono text-xs">{r.destino_minio_prefix}</td>
                    <td className="px-3 py-2 text-xs">{formatDt(r.proxima_ejecucion)}</td>
                    <td className="px-3 py-2 text-xs">{formatDt(r.ultima_ejecucion)}</td>
                    <td className="px-3 py-2">
                      <Badge tone={r.activo ? 'green' : 'slate'}>
                        {r.ultimo_estado || '—'}
                      </Badge>
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex gap-1">
                        <button
                          type="button"
                          title="Ejecutar ahora (manual)"
                          className="rounded-lg p-2 hover:bg-slate-100"
                          disabled={runningId === r.id}
                          onClick={() => ejecutar(r.id)}
                        >
                          <Play className="h-4 w-4 text-brand-600" />
                        </button>
                        <button
                          type="button"
                          title="Editar"
                          className="rounded-lg p-2 hover:bg-slate-100"
                          onClick={() => openEdit(r)}
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          <Card className="mb-6 border-amber-100 bg-amber-50/40 p-6">
            <h3 className="flex items-center gap-2 font-semibold text-slate-900">
              <Upload className="h-4 w-4 text-amber-700" />
              Restaurar desde ZIP (tu PC)
            </h3>
            <p className="mt-1 text-sm text-slate-600">
              Si eliminaste datos en MinIO, sube el ZIP descargado antes. La restauración y el ETL
              se ejecutan solos; verás el progreso abajo (puede tardar 15–30 min con muchos registros).
            </p>
            <div className="mt-4 flex flex-wrap items-end gap-3">
              <input
                type="file"
                accept=".zip,application/zip"
                onChange={(e) => setRestoreFile(e.target.files?.[0] || null)}
                className="text-sm"
                disabled={restoring}
              />
              <Button type="button" onClick={restaurarZip} disabled={restoring || !restoreFile}>
                {restoring ? 'Restaurando + ETL…' : 'Restaurar y ejecutar ETL'}
              </Button>
            </div>
            <div className="mt-4">
              <RestoreProgressCard
                progress={restoreProgress}
                running={restoring}
                onCancel={cancelRestore}
                canCancel={canCancel}
              />
            </div>
          </Card>

          <Card className="overflow-x-auto">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3">
              <div>
                <h3 className="flex items-center gap-2 font-semibold text-slate-900">
                  <History className="h-4 w-4" />
                  Historial de respaldos
                </h3>
                <p className="mt-0.5 text-xs text-slate-500">
                  Solo ejecuciones manuales (botón Ejecutar). Los programados no llenan esta lista.
                </p>
              </div>
              {selectedHist.size > 0 && (
                <Button
                  type="button"
                  variant="secondary"
                  className="border-red-200 text-red-700 hover:bg-red-50"
                  onClick={() =>
                    confirmDeleteHistorial(
                      [...selectedHist],
                      `${selectedHist.size} registro(s) seleccionado(s)`
                    )
                  }
                >
                  <Trash2 className="h-4 w-4" />
                  Eliminar seleccionados ({selectedHist.size})
                </Button>
              )}
            </div>
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="w-10 px-3 py-2">
                    <input
                      type="checkbox"
                      title="Seleccionar todos"
                      checked={allDeletableSelected && deletableHistorial.length > 0}
                      disabled={deletableHistorial.length === 0}
                      onChange={toggleSelectAllHist}
                      className="rounded border-slate-300"
                    />
                  </th>
                  <th className="px-3 py-2 text-left">Inicio</th>
                  <th className="px-3 py-2 text-left">Configuración</th>
                  <th className="px-3 py-2 text-left">Tipo</th>
                  <th className="px-3 py-2 text-left">Origen</th>
                  <th className="px-3 py-2 text-left">Tablas</th>
                  <th className="px-3 py-2">Estado</th>
                  <th className="px-3 py-2 text-left">Detalle</th>
                  <th className="px-3 py-2 text-center">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {historial.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-3 py-8 text-center text-slate-500">
                      Aún no hay ejecuciones registradas.
                    </td>
                  </tr>
                ) : (
                  historial.map((h) => (
                    <tr key={h.id} className="border-t">
                      <td className="px-3 py-2">
                        <input
                          type="checkbox"
                          checked={selectedHist.has(h.id)}
                          disabled={!canDeleteHistorial(h)}
                          title={
                            canDeleteHistorial(h)
                              ? 'Seleccionar'
                              : 'No se puede eliminar en ejecución'
                          }
                          onChange={() => toggleHistSelect(h.id)}
                          className="rounded border-slate-300 disabled:opacity-40"
                        />
                      </td>
                      <td className="px-3 py-2 text-xs whitespace-nowrap">
                        {formatDt(h.iniciado_en)}
                      </td>
                      <td className="px-3 py-2">{h.nombre_config}</td>
                      <td className="px-3 py-2 capitalize">{h.tipo_respaldo}</td>
                      <td className="px-3 py-2">
                        <Badge tone="blue">Manual</Badge>
                      </td>
                      <td className="px-3 py-2 font-mono">{h.tablas_copiadas ?? 0}</td>
                      <td className="px-3 py-2">
                        <Badge tone={estadoTone(h.estado)}>{h.estado}</Badge>
                      </td>
                      <td className="max-w-xs truncate px-3 py-2 text-xs text-slate-600">
                        {h.detalle}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex items-center justify-center gap-1">
                          {String(h.estado).toLowerCase() === 'completado' ? (
                            <button
                              type="button"
                              title="Descargar ZIP"
                              className="rounded-lg p-2 hover:bg-slate-100"
                              onClick={() => descargar(h.id)}
                            >
                              <Download className="h-4 w-4 text-brand-600" />
                            </button>
                          ) : null}
                          {canDeleteHistorial(h) ? (
                            <button
                              type="button"
                              title="Eliminar del historial"
                              className="rounded-lg p-2 hover:bg-red-50"
                              onClick={() =>
                                confirmDeleteHistorial(
                                  [h.id],
                                  `respaldo del ${formatDt(h.iniciado_en)}`
                                )
                              }
                            >
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </button>
                          ) : (
                            <span className="px-2 text-xs text-slate-400">—</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </Card>

          <ConfirmDialog
            open={!!deleteDialog}
            title="Eliminar del historial"
            message={
              deleteDialog
                ? `¿Eliminar ${deleteDialog.label}? Se borrará el registro y los archivos asociados en MinIO (si existen). Esta acción no se puede deshacer.`
                : ''
            }
            loading={deletingHist}
            onConfirm={runDeleteHistorial}
            onCancel={() => !deletingHist && setDeleteDialog(null)}
          />
        </>
      )}
    </AdminGuard>
  )
}
