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
import { displayTablasCount, formatBackupEstado, LOGICAL_TABLES_COMPLETO, TX_TABLES_COMPLETO, ADMIN_TABLES_COMPLETO } from '../../utils/backupDisplay'

const FRECUENCIAS = [
  { value: 'horario', label: 'Horario (cada 24 h)' },
  { value: 'diario', label: 'Diario' },
  { value: 'semanal', label: 'Semanal' },
  { value: 'mensual', label: 'Mensual' },
]

const TIPOS = [
  {
    value: 'completo',
    label: `Completo (${TX_TABLES_COMPLETO} transaccionales + ${ADMIN_TABLES_COMPLETO} administración)`,
  },
  { value: 'incremental', label: 'Incremental (sesiones y auditoría)' },
]

const INPUT =
  'w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2.5 text-sm text-slate-900 transition focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-100'

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

function normalizeTimeInput(value) {
  if (!value) return '02:00'
  const match = String(value).match(/(\d{1,2}):(\d{2})/)
  if (!match) return '02:00'
  return `${match[1].padStart(2, '0')}:${match[2]}`
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
      await adminApi.respaldosProgramados().catch(() => {})
      const [cfg, hist] = await Promise.all([
        adminApi.respaldos(false),
        adminApi.respaldosHistorial(100, false),
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
      hora_programada: normalizeTimeInput(row.hora_programada),
      activo: Boolean(row.activo),
    })
    setFormOpen(true)
  }

  const saveConfig = async (e) => {
    e.preventDefault()
    const payload = {
      ...form,
      hora_programada: normalizeTimeInput(form.hora_programada),
    }
    try {
      if (editing) {
        await adminApi.updateRespaldo(editing.id, payload)
        toast.success('Éxito', 'Configuración actualizada')
      } else {
        await adminApi.createRespaldoConfig(payload)
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
        toast.success('Éxito', r.detalle || `Respaldo OK (${r.tablas_copiadas ?? 0} tablas)`)
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

      <Card className="mb-6 border-slate-200/80 bg-gradient-to-br from-slate-50/80 to-white">
        <p className="text-sm leading-relaxed text-slate-600">
          El respaldo <strong className="text-slate-800">completo</strong> incluye{' '}
          <strong className="text-slate-800">{LOGICAL_TABLES_COMPLETO} tablas lógicas</strong> (
          {TX_TABLES_COMPLETO} transaccionales — asignaciones, bitácora, evidencias, etc. — más{' '}
          {ADMIN_TABLES_COMPLETO} de administración), la capa analítica MinIO (dimensiones +
          hechos) y el resumen del dashboard. Al restaurar un ZIP completo no hace falta ETL desde
          PocketBase. Los respaldos anteriores pueden mostrar{' '}
          <strong className="text-slate-800">16 tablas</strong>; desde el próximo respaldo verás{' '}
          <strong className="text-slate-800">{LOGICAL_TABLES_COMPLETO}</strong>.
        </p>
      </Card>

      {formOpen && (
        <Card className="mb-6 border-brand-200/60 bg-gradient-to-br from-brand-50/40 to-white">
          <form onSubmit={saveConfig} className="space-y-4">
            <h3 className="border-b border-slate-100 pb-3 text-base font-semibold text-slate-900">
              {editing ? 'Editar programación' : 'Nueva programación de respaldo'}
            </h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block sm:col-span-2">
                <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Nombre
                </span>
                <input
                  value={form.nombre}
                  onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                  className={INPUT}
                  required
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Frecuencia
                </span>
                <select
                  value={form.frecuencia}
                  onChange={(e) => setForm({ ...form, frecuencia: e.target.value })}
                  className={INPUT}
                >
                  {FRECUENCIAS.map((f) => (
                    <option key={f.value} value={f.value}>
                      {f.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Hora programada
                </span>
                <input
                  type="time"
                  value={form.hora_programada}
                  onChange={(e) => setForm({ ...form, hora_programada: e.target.value })}
                  className={INPUT}
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Tipo de respaldo
                </span>
                <select
                  value={form.tipo_respaldo}
                  onChange={(e) => setForm({ ...form, tipo_respaldo: e.target.value })}
                  className={INPUT}
                >
                  {TIPOS.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Destino MinIO (prefijo)
                </span>
                <input
                  value={form.destino_minio_prefix}
                  onChange={(e) =>
                    setForm({ ...form, destino_minio_prefix: e.target.value })
                  }
                  className={`${INPUT} font-mono`}
                  required
                />
              </label>
              <label className="flex cursor-pointer items-center gap-2.5 rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2.5 sm:col-span-2">
                <input
                  type="checkbox"
                  checked={form.activo}
                  onChange={(e) => setForm({ ...form, activo: e.target.checked })}
                  className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                />
                <span className="text-sm font-medium text-slate-700">Programación activa</span>
              </label>
            </div>
            <div className="flex gap-2 border-t border-slate-100 pt-4">
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
          <Card className="mb-6 overflow-hidden p-0">
            <div className="border-b border-slate-100 bg-slate-50/80 px-5 py-3">
              <h3 className="text-sm font-semibold text-slate-900">Programaciones activas</h3>
            </div>
            <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-200 bg-slate-50/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Nombre</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Frecuencia</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Hora</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Tipo</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Destino</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Próxima</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Última</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Estado</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {items.map((r) => (
                  <tr key={r.id} className="border-b border-slate-100 transition hover:bg-slate-50/60">
                    <td className="px-4 py-3 font-medium text-slate-900">{r.nombre}</td>
                    <td className="px-4 py-3 text-slate-700">{r.frecuencia}</td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-700">
                      {normalizeTimeInput(r.hora_programada)}
                    </td>
                    <td className="px-4 py-3 capitalize text-slate-700">{r.tipo_respaldo || 'completo'}</td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-500">{r.destino_minio_prefix}</td>
                    <td className="px-4 py-3 text-xs text-slate-600">{formatDt(r.proxima_ejecucion)}</td>
                    <td className="px-4 py-3 text-xs text-slate-600">{formatDt(r.ultima_ejecucion)}</td>
                    <td className="px-4 py-3">
                      <Badge tone={r.activo ? 'green' : 'slate'} title={r.ultimo_estado}>
                        {formatBackupEstado(r.ultimo_estado)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-0.5">
                        <button
                          type="button"
                          title="Ejecutar ahora (manual)"
                          className="rounded-lg p-2 text-slate-500 transition hover:bg-brand-50 hover:text-brand-600 disabled:opacity-50"
                          disabled={runningId === r.id}
                          onClick={() => ejecutar(r.id)}
                        >
                          <Play className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          title="Editar"
                          className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
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
            </div>
          </Card>

          <Card className="mb-6 overflow-hidden border-amber-200/60 bg-gradient-to-br from-amber-50/60 to-white">
            <div className="border-b border-amber-100/80 bg-amber-50/50 px-5 py-4">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
                  <Upload className="h-4 w-4" />
                </div>
                Restaurar desde ZIP (tu PC)
              </h3>
            </div>
            <div className="p-5">
            <p className="text-sm leading-relaxed text-slate-600">
              Si eliminaste datos en MinIO, sube el ZIP completo descargado antes. Con analítica
              incluida la restauración es mucho más rápida (sin ETL de 320k desde PocketBase).
            </p>
            <div className="mt-4 flex flex-wrap items-end gap-3">
              <input
                type="file"
                accept=".zip,application/zip"
                onChange={(e) => setRestoreFile(e.target.files?.[0] || null)}
                className="text-sm file:mr-3 file:rounded-xl file:border-0 file:bg-brand-50 file:px-4 file:py-2 file:text-sm file:font-medium file:text-brand-700"
                disabled={restoring}
              />
              <Button type="button" onClick={restaurarZip} disabled={restoring || !restoreFile}>
                {restoring ? 'Restaurando…' : 'Restaurar desde ZIP'}
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
            </div>
          </Card>

          <Card className="overflow-hidden p-0">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 bg-slate-50/80 px-5 py-4">
              <div>
                <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <History className="h-4 w-4 text-brand-600" />
                  Historial de respaldos
                </h3>
                <p className="mt-0.5 text-xs text-slate-500">
                  Manuales y automáticos. La hora programada usa zona{' '}
                  <strong>America/Bogota</strong>. Requiere Celery Beat activo o abrir esta página.
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
            <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-200 bg-slate-50/50">
                <tr>
                  <th className="w-10 px-4 py-3">
                    <input
                      type="checkbox"
                      title="Seleccionar todos"
                      checked={allDeletableSelected && deletableHistorial.length > 0}
                      disabled={deletableHistorial.length === 0}
                      onChange={toggleSelectAllHist}
                      className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                    />
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Inicio</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Configuración</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Tipo</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Origen</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Tablas</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Estado</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Detalle</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-slate-500">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {historial.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-12 text-center text-sm text-slate-500">
                      Aún no hay ejecuciones registradas.
                    </td>
                  </tr>
                ) : (
                  historial.map((h) => (
                    <tr key={h.id} className="border-b border-slate-100 transition hover:bg-slate-50/60">
                      <td className="px-4 py-3">
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
                          className="rounded border-slate-300 text-brand-600 focus:ring-brand-500 disabled:opacity-40"
                        />
                      </td>
                      <td className="px-4 py-3 text-xs whitespace-nowrap text-slate-600">
                        {formatDt(h.iniciado_en)}
                      </td>
                      <td className="px-4 py-3 text-slate-800">{h.nombre_config}</td>
                      <td className="px-4 py-3 capitalize text-slate-700">{h.tipo_respaldo}</td>
                      <td className="px-4 py-3">
                        <Badge tone="blue">Manual</Badge>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-600">
                        {displayTablasCount(h.tablas_copiadas)}
                      </td>
                      <td className="px-4 py-3">
                        <Badge tone={estadoTone(h.estado)}>{h.estado}</Badge>
                      </td>
                      <td
                        className="max-w-xs truncate px-4 py-3 text-xs text-slate-500"
                        title={h.detalle}
                      >
                        {formatBackupEstado(h.detalle)}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-center gap-0.5">
                          {String(h.estado).toLowerCase() === 'completado' ? (
                            <button
                              type="button"
                              title="Descargar ZIP"
                              className="rounded-lg p-2 text-slate-500 transition hover:bg-brand-50 hover:text-brand-600"
                              onClick={() => descargar(h.id)}
                            >
                              <Download className="h-4 w-4" />
                            </button>
                          ) : null}
                          {canDeleteHistorial(h) ? (
                            <button
                              type="button"
                              title="Eliminar del historial"
                              className="rounded-lg p-2 text-slate-500 transition hover:bg-red-50 hover:text-red-600"
                              onClick={() =>
                                confirmDeleteHistorial(
                                  [h.id],
                                  `respaldo del ${formatDt(h.iniciado_en)}`
                                )
                              }
                            >
                              <Trash2 className="h-4 w-4" />
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
            </div>
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
