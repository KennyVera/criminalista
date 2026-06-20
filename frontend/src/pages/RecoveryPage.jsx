import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  Download,
  HardDrive,
  ShieldAlert,
  Upload,
  LogIn,
} from 'lucide-react'
import { recoveryApi } from '../api/recovery'
import { api } from '../api/client'
import RestoreProgressCard from '../components/RestoreProgressCard'
import { Button, Card, Badge, Spinner, Input } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { useRestoreWithEtl } from '../hooks/useRestoreWithEtl'

const RECOVERY_TOKEN_KEY = 'crimetrack_recovery_token'

function formatDt(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('es-CO')
  } catch {
    return iso
  }
}

export default function RecoveryPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const [status, setStatus] = useState(null)
  const [authenticated, setAuthenticated] = useState(
    () => !!sessionStorage.getItem(RECOVERY_TOKEN_KEY)
  )
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loggingIn, setLoggingIn] = useState(false)
  const [historial, setHistorial] = useState([])
  const [restoreFile, setRestoreFile] = useState(null)
  const {
    run: runRestoreWithEtl,
    running: restoring,
    progress: restoreProgress,
    cancel: cancelRestore,
    canCancel,
  } = useRestoreWithEtl({
    startRestore: recoveryApi.restaurar,
    getStatus: recoveryApi.restaurarEstado,
    cancelRestore: recoveryApi.cancelarRestaurar,
  })

  const loadStatus = useCallback(async () => {
    const s = await recoveryApi.estado()
    setStatus(s)
    if (!s.recovery_required) {
      sessionStorage.removeItem(RECOVERY_TOKEN_KEY)
      api.setAuthToken(null)
      navigate('/login', { replace: true })
    }
    return s
  }, [navigate])

  const loadHistorial = useCallback(async () => {
    if (!sessionStorage.getItem(RECOVERY_TOKEN_KEY)) return
    try {
      const h = await recoveryApi.historial()
      setHistorial(h.items || [])
    } catch {
      setHistorial([])
    }
  }, [])

  useEffect(() => {
    const token = sessionStorage.getItem(RECOVERY_TOKEN_KEY)
    if (token) api.setAuthToken(token)
    loadStatus()
  }, [loadStatus])

  useEffect(() => {
    if (authenticated) loadHistorial()
  }, [authenticated, loadHistorial])

  const handleRecoveryLogin = async (e) => {
    e.preventDefault()
    setLoggingIn(true)
    try {
      const data = await recoveryApi.login(email.trim(), password)
      sessionStorage.setItem(RECOVERY_TOKEN_KEY, data.access_token)
      api.setAuthToken(data.access_token)
      setAuthenticated(true)
      toast.success('Acceso de recuperación', data.message)
      loadHistorial()
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setLoggingIn(false)
    }
  }

  const restaurar = async () => {
    if (!restoreFile) {
      toast.warning('Atención', 'Selecciona el archivo ZIP de respaldo')
      return
    }
    try {
      const r = await runRestoreWithEtl(restoreFile)
      if (r?.cancelled) {
        toast.info('Cancelado', r?.message || 'Se restauró el estado anterior en MinIO.')
        return
      }
      toast.success('Restauración + ETL', r?.message || 'Proceso completado.')
      setRestoreFile(null)
      const s = await loadStatus()
      if (!s?.recovery_required) {
        sessionStorage.removeItem(RECOVERY_TOKEN_KEY)
        navigate('/login', { replace: true })
      }
    } catch (err) {
      toast.error('Error', err.message)
    }
  }

  if (!status) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 p-4 sm:p-6 dark:bg-slate-950">
      <div className="mx-auto max-w-3xl space-y-6 animate-fade-up">
        <Card className="border-red-200/80 p-6 dark:border-red-900/50">
          <div className="flex gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-700 ring-1 ring-red-200 dark:bg-red-950/50 dark:text-red-300 dark:ring-red-900">
              <ShieldAlert className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50">Modo recuperación</h1>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{status.message}</p>
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-500">
                Los demás usuarios ven la pantalla de mantenimiento. Solo el administrador puede
                restaurar datos desde aquí.
              </p>
            </div>
          </div>
        </Card>

        {!authenticated ? (
          <Card className="p-6">
            <h2 className="mb-4 flex items-center gap-2 font-semibold text-slate-900">
              <LogIn className="h-4 w-4" />
              Acceso de administrador (recuperación)
            </h2>
            <p className="mb-4 text-sm text-slate-600">
              Use las credenciales de recuperación configuradas en el servidor (
              <code className="rounded bg-slate-100 px-1">CRIMETRACK_RECOVERY_EMAIL</code> /{' '}
              <code className="rounded bg-slate-100 px-1">CRIMETRACK_RECOVERY_PASSWORD</code>
              ). Por defecto coinciden con el admin inicial del sistema.
            </p>
            <form onSubmit={handleRecoveryLogin} className="max-w-md space-y-3">
              <Input
                type="email"
                placeholder="Correo administrador"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <Input
                type="password"
                placeholder="Contraseña de recuperación"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <Button type="submit" disabled={loggingIn}>
                {loggingIn ? 'Verificando…' : 'Entrar al panel de recuperación'}
              </Button>
            </form>
          </Card>
        ) : (
          <>
            <Card className="border-amber-200/80 bg-amber-50/30 p-6 dark:border-amber-900/50 dark:bg-amber-950/20">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 shrink-0 text-amber-700" />
                <div className="text-sm text-amber-950">
                  <p className="font-medium">Restaure el respaldo ZIP descargado previamente.</p>
                  <p className="mt-1">
                    El ETL del modelo estrella se ejecuta automáticamente tras la restauración.
                    Espere a que el progreso llegue al 100% antes de volver al login.
                  </p>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h2 className="mb-4 flex items-center gap-2 font-semibold">
                <Upload className="h-4 w-4" />
                Restaurar desde ZIP
              </h2>
              <div className="flex flex-wrap items-end gap-3">
                <input
                  type="file"
                  accept=".zip"
                  onChange={(e) => setRestoreFile(e.target.files?.[0] || null)}
                  className="text-sm"
                  disabled={restoring}
                />
                <Button type="button" onClick={restaurar} disabled={restoring || !restoreFile}>
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

            <Card className="overflow-hidden p-0">
              <h2 className="flex items-center gap-2 border-b border-slate-200/80 px-4 py-3 font-semibold dark:border-slate-800">
                <HardDrive className="h-4 w-4" />
                Historial de respaldos en MinIO
              </h2>
              {historial.length === 0 ? (
                <p className="px-4 py-8 text-center text-sm text-slate-500 dark:text-slate-400">
                  No hay historial en MinIO (también fue eliminado). Suba directamente el ZIP que
                  guardó en su PC.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Fecha</th>
                        <th>Configuración</th>
                        <th>Estado</th>
                        <th>ZIP</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historial.map((h) => (
                        <tr key={h.id}>
                          <td className="text-xs">{formatDt(h.iniciado_en)}</td>
                          <td>{h.nombre_config}</td>
                          <td>
                            <Badge
                              tone={
                                String(h.estado).toLowerCase() === 'completado' ? 'green' : 'red'
                              }
                            >
                              {h.estado}
                            </Badge>
                          </td>
                          <td>
                            {String(h.estado).toLowerCase() === 'completado' ? (
                              <button
                                type="button"
                                className="rounded-lg p-2 transition hover:bg-slate-100 dark:hover:bg-slate-800"
                                title="Descargar"
                                onClick={() => recoveryApi.download(h.id)}
                              >
                                <Download className="h-4 w-4 text-indigo-600" />
                              </button>
                            ) : (
                              '—'
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </>
        )}
      </div>
    </div>
  )
}
