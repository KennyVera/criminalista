import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { AppConfigProvider } from './context/AppConfigContext'
import { ThemeProvider } from './context/ThemeContext'
import { ToastProvider } from './context/ToastContext'
import ProtectedRoute from './components/ProtectedRoute'
import DashboardLayout from './layouts/DashboardLayout'
import Dashboard from './pages/Dashboard'
import CollectionCrud from './pages/CollectionCrud'
import GenerateDataPage from './pages/GenerateDataPage'
import LoginPage from './pages/LoginPage'
import RecoverPasswordPage from './pages/RecoverPasswordPage'
import ActiveSessionsPage from './pages/ActiveSessionsPage'
import AdminUsersPage from './pages/admin/AdminUsersPage'
import AdminPermissionsPage from './pages/admin/AdminPermissionsPage'
import AdminPoliciesPage from './pages/admin/AdminPoliciesPage'
import AdminParametersPage from './pages/admin/AdminParametersPage'
import AdminBackupsPage from './pages/admin/AdminBackupsPage'
import AdminCrimeCatalogsPage from './pages/admin/AdminCrimeCatalogsPage'
import AdminZonesPage from './pages/admin/AdminZonesPage'
import AdminSystemStatusPage from './pages/admin/AdminSystemStatusPage'

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <ToastProvider>
          <AppConfigProvider>
            <BrowserRouter>
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
            </Routes>
            </BrowserRouter>
          </AppConfigProvider>
        </ToastProvider>
      </ThemeProvider>
    </AuthProvider>
  )
}