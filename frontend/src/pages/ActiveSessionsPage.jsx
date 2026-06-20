import { useCallback, useEffect, useState } from 'react'
import {
  LogOut,
  Monitor,
  RefreshCw,
  Shield,
  Lock,
  Fingerprint,
  CheckCircle2,
  Users,
  Database,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Badge, Button, Card, Spinner } from '../components/ui'
import PageHeader from '../components/layout/PageHeader'
import StatCard from '../components/layout/StatCard'
import UserCell from '../components/layout/UserCell'
import TablePagination from '../components/layout/TablePagination'
import InfoPanel from '../components/layout/InfoPanel'
import RowActionsMenu from '../components/layout/RowActionsMenu'
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
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(10)
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
  }, [toast])

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
      <Card className="border-amber-200/80">
        <p className="font-semibold text-amber-900 dark:text-amber-200">Acceso restringido</p>
        <p className="mt-1 text-sm text-amber-800 dark:text-amber-300">
          Solo el rol Admin puede gestionar sesiones activas.
        </p>
      </Card>
    )
  }

  const totalPages = Math.max(1, Math.ceil(items.length / perPage))
  const pageItems = items.slice((page - 1) * perPage, page * perPage)

  return (
    <section className="space-y-6 animate-fade-up">
      <PageHeader
        title="Sesiones activas"
        subtitle="Paquete Autenticación y Seguridad — dataset en MinIO"
        dataset="app_sesiones_activas"
        icon={Monitor}
        actions={
          <Button type="button" variant="secondary" onClick={load} disabled={loading}>
            <RefreshCw className={cnSpin(loading)} />
            Actualizar
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Sesiones en curso"
          value={total}
          sub="Usuarios conectados"
          sparkline="blue"
          icon={Users}
        />
        <StatCard
          label="Fuente"
          value="MinIO Parquet"
          sub="Almacenamiento de datos"
          sparkline="green"
          icon={Database}
        />
        <StatCard
          label="Tu rol"
          value={user?.nombre_rol || '—'}
          sub="Acceso total al sistema"
          sparkline="purple"
          icon={Shield}
        />
      </div>

      <Card flush className="overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-20">
            <Spinner />
          </div>
        ) : items.length === 0 ? (
          <p className="py-20 text-center body-text">
            No hay sesiones activas en este momento.
          </p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="data-table min-w-[960px]">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Usuario</th>
                    <th>Rol</th>
                    <th>Placa</th>
                    <th>IP</th>
                    <th>Inicio de sesión</th>
                    <th>Último acceso</th>
                    <th>Expira</th>
                    <th>Estado</th>
                    <th className="text-center">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {pageItems.map((row) => (
                    <tr key={row.id_sesion || row.token_jti}>
                      <td className="font-mono caption-text">{row.id_sesion}</td>
                      <td>
                        <UserCell
                          name={`${row.nombres || ''} ${row.apellidos || ''}`.trim()}
                          email={row.email}
                        />
                      </td>
                      <td>
                        <Badge tone="info">{row.nombre_rol}</Badge>
                      </td>
                      <td className="font-mono caption-text">
                        {row.numero_placa || '—'}
                      </td>
                      <td className="font-mono caption-text">
                        {row.direccion_ip || '—'}
                      </td>
                      <td className="caption-text">
                        {formatDate(row.fecha_inicio)}
                      </td>
                      <td className="caption-text">
                        {formatDate(row.fecha_ultimo_acceso)}
                      </td>
                      <td className="caption-text">
                        {formatDate(row.fecha_expiracion)}
                      </td>
                      <td>
                        <Badge tone="active">Activa</Badge>
                      </td>
                      <td className="text-center">
                        <RowActionsMenu
                          items={[
                            {
                              label: 'Cerrar sesión',
                              icon: LogOut,
                              danger: true,
                              disabled: closingId === row.id_sesion,
                              onClick: () => handleCloseSession(row),
                            },
                          ]}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <TablePagination
              page={page}
              totalPages={totalPages}
              totalItems={items.length}
              perPage={perPage}
              onPageChange={setPage}
              onPerPageChange={(n) => {
                setPerPage(n)
                setPage(1)
              }}
              itemLabel={items.length === 1 ? 'sesión' : 'sesiones'}
            />
          </>
        )}
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <InfoPanel title="Seguridad avanzada" icon={Lock}>
          <p className="flex items-center gap-1.5 text-emerald-700 dark:text-emerald-400">
            <CheckCircle2 className="h-4 w-4" />
            Sistema protegido
          </p>
          <p className="mt-1 text-xs">Sesiones firmadas con JWT y revocación en tiempo real.</p>
        </InfoPanel>
        <InfoPanel
          title="Acceso controlado"
          icon={Fingerprint}
          action={
            <Link
              to="/admin/politicas"
              className="text-xs font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400"
            >
              Ver auditoría →
            </Link>
          }
        >
          <p className="text-xs">Políticas RBAC y control por rol institucional.</p>
        </InfoPanel>
        <InfoPanel title="Recomendaciones" icon={Shield}>
          <ul className="space-y-1 text-xs">
            <li>· Revise sesiones inusuales semanalmente</li>
            <li>· Cierre sesiones de personal dado de baja</li>
            <li>· Verifique IPs desde redes autorizadas</li>
          </ul>
        </InfoPanel>
      </div>
    </section>
  )
}

function cnSpin(loading) {
  return loading ? 'h-4 w-4 animate-spin' : 'h-4 w-4'
}
