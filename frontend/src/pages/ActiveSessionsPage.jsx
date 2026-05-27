import { useCallback, useEffect, useState } from 'react'
import { LogOut, Monitor, RefreshCw, Shield } from 'lucide-react'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Badge, Button, Card, Spinner } from '../components/ui'
import { useToast } from '../context/ToastContext'

function formatDate(value) {
  if (!value) return '—'
  try {
    return new Date(value).toLocaleString('es-CO')
  } catch {
    return String(value)
  }
}

export default function ActiveSessionsPage() {
  const { user } = useAuth()
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const toast = useToast()
  const [closingId, setClosingId] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.authActiveSessions()
      setItems(data.items || [])
      setTotal(data.total ?? 0)
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleCloseSession = async (row) => {
    const label = `${row.nombres || ''} ${row.apellidos || ''}`.trim() || row.email
    if (
      !window.confirm(
        `¿Cerrar la sesión de ${label}? El usuario verá un aviso y deberá iniciar sesión de nuevo.`
      )
    ) {
      return
    }
    setClosingId(row.id_sesion)
    try {
      await api.authCloseSession(row.id_sesion)
      toast.success('Éxito', 'Sesión cerrada correctamente')
      await load()
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setClosingId(null)
    }
  }

  if (user?.nombre_rol?.toLowerCase() !== 'admin') {
    return (
      <Card className="border-amber-200 bg-amber-50">
        <p className="font-medium text-amber-900">Acceso restringido</p>
        <p className="mt-1 text-sm text-amber-800">
          Solo el rol Admin puede gestionar sesiones activas.
        </p>
      </Card>
    )
  }

  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="flex items-center gap-2 text-xl font-bold text-slate-900">
            <Monitor className="h-6 w-6 text-brand-600" />
            Sesiones activas
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Paquete Autenticación y Seguridad — dataset en MinIO (
            <code className="text-xs">app_sesiones_activas</code>)
          </p>
        </div>
        <Button type="button" variant="secondary" onClick={load} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </header>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <p className="text-sm text-slate-500">Sesiones en curso</p>
          <p className="mt-1 text-3xl font-bold text-brand-600">{total}</p>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Fuente</p>
          <p className="mt-1 font-medium text-slate-800">MinIO Parquet</p>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Tu rol</p>
          <p className="mt-1 flex items-center gap-2 font-medium text-slate-800">
            <Shield className="h-4 w-4 text-emerald-600" />
            {user?.nombre_rol}
          </p>
        </Card>
      </div>

      <Card>
        {loading ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : items.length === 0 ? (
          <p className="py-12 text-center text-sm text-slate-500">
            No hay sesiones activas en este momento.
          </p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full min-w-[960px] text-left text-sm">
              <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-3">ID</th>
                  <th className="px-3 py-3">Usuario</th>
                  <th className="px-3 py-3">Rol</th>
                  <th className="px-3 py-3">Placa</th>
                  <th className="px-3 py-3">IP</th>
                  <th className="px-3 py-3">Inicio</th>
                  <th className="px-3 py-3">Último acceso</th>
                  <th className="px-3 py-3">Expira</th>
                  <th className="px-3 py-3">Estado</th>
                  <th className="px-3 py-3 text-center">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={row.id_sesion || row.token_jti} className="border-t border-slate-100">
                    <td className="px-3 py-2.5 font-mono text-xs">{row.id_sesion}</td>
                    <td className="px-3 py-2.5">
                      <p className="font-medium text-slate-900">
                        {row.nombres} {row.apellidos}
                      </p>
                      <p className="text-xs text-slate-500">{row.email}</p>
                    </td>
                    <td className="px-3 py-2.5">{row.nombre_rol}</td>
                    <td className="px-3 py-2.5">{row.numero_placa}</td>
                    <td className="px-3 py-2.5 font-mono text-xs">{row.direccion_ip || '—'}</td>
                    <td className="px-3 py-2.5 text-xs">{formatDate(row.fecha_inicio)}</td>
                    <td className="px-3 py-2.5 text-xs">{formatDate(row.fecha_ultimo_acceso)}</td>
                    <td className="px-3 py-2.5 text-xs">{formatDate(row.fecha_expiracion)}</td>
                    <td className="px-3 py-2.5">
                      <Badge tone="green">Activa</Badge>
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <button
                        type="button"
                        title="Cerrar sesión"
                        aria-label={`Cerrar sesión de ${row.email}`}
                        disabled={closingId === row.id_sesion}
                        onClick={() => handleCloseSession(row)}
                        className="inline-flex cursor-pointer items-center justify-center rounded-lg p-2 text-slate-500 transition hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <LogOut className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </section>
  )
}
