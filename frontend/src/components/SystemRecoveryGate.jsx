import { useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { recoveryApi } from '../api/recovery'
import { Spinner } from './ui'
import MaintenancePage from '../pages/MaintenancePage'
import RecoveryPage from '../pages/RecoveryPage'
import LoginPage from '../pages/LoginPage'
import RecoverPasswordPage from '../pages/RecoverPasswordPage'
import ProtectedRoute from './ProtectedRoute'
import DashboardLayout from '../layouts/DashboardLayout'
import Dashboard from '../pages/Dashboard'
import CollectionCrud from '../pages/CollectionCrud'
import GenerateDataPage from '../pages/GenerateDataPage'
import ActiveSessionsPage from '../pages/ActiveSessionsPage'
import AdminUsersPage from '../pages/admin/AdminUsersPage'
import AdminPermissionsPage from '../pages/admin/AdminPermissionsPage'
import AdminPoliciesPage from '../pages/admin/AdminPoliciesPage'
import AdminParametersPage from '../pages/admin/AdminParametersPage'
import AdminBackupsPage from '../pages/admin/AdminBackupsPage'
import AdminCrimeCatalogsPage from '../pages/admin/AdminCrimeCatalogsPage'
import AdminZonesPage from '../pages/admin/AdminZonesPage'
import AdminSystemStatusPage from '../pages/admin/AdminSystemStatusPage'

const POLL_MS = 20_000

function NormalAppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/recuperar-contrasena" element={<RecoverPasswordPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="tabla/:slug" element={<CollectionCrud />} />
        <Route path="generar-datos" element={<GenerateDataPage />} />
        <Route path="seguridad/sesiones-activas" element={<ActiveSessionsPage />} />
        <Route path="admin/usuarios" element={<AdminUsersPage />} />
        <Route path="admin/permisos" element={<AdminPermissionsPage />} />
        <Route path="admin/politicas" element={<AdminPoliciesPage />} />
        <Route path="admin/parametros" element={<AdminParametersPage />} />
        <Route path="admin/respaldos" element={<AdminBackupsPage />} />
        <Route path="admin/catalogos" element={<AdminCrimeCatalogsPage />} />
        <Route path="admin/zonas" element={<AdminZonesPage />} />
        <Route path="admin/estado-sistema" element={<AdminSystemStatusPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
      <Route path="/recuperacion" element={<Navigate to="/" replace />} />
      <Route path="/mantenimiento" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function SystemRecoveryGate() {
  const [status, setStatus] = useState(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const s = await recoveryApi.estado()
        if (!cancelled) setStatus(s)
      } catch {
        if (!cancelled) {
          setStatus({
            recovery_required: true,
            message: 'No se pudo verificar el estado del sistema.',
          })
        }
      }
    }
    load()
    const id = setInterval(load, POLL_MS)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  if (!status) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner />
      </div>
    )
  }

  if (status.recovery_required) {
    return (
      <Routes>
        <Route path="/recuperacion" element={<RecoveryPage />} />
        <Route path="/login" element={<Navigate to="/recuperacion" replace />} />
        <Route path="/recuperar-contrasena" element={<Navigate to="/mantenimiento" replace />} />
        <Route
          path="/mantenimiento"
          element={<MaintenancePage message={status.message} />}
        />
        <Route path="*" element={<Navigate to="/mantenimiento" replace />} />
      </Routes>
    )
  }

  return <NormalAppRoutes />
}
