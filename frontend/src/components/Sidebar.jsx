import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  ChevronDown,
  ChevronLeft,
  Shield,
  Database,
  Table2,
  Monitor,
  Users,
  KeyRound,
  ShieldCheck,
  Settings,
  HardDrive,
  BookOpen,
  MapPin,
  Activity,
  UserCheck,
  ClipboardList,
} from 'lucide-react'
import GenerateDataButton from './GenerateDataButton'
import { useAuth } from '../context/AuthContext'
import {
  canAccessAdmin,
  canAccessDataCrud,
  canManageAsignaciones,
  canViewInvestigacionProgress,
} from '../utils/roles'

export default function Sidebar({
  collections,
  collapsed,
  onToggle,
  appName = 'CrimeTrack Analytics',
  appSubtitle = 'Analytics Corp',
  appIconUrl = '',
}) {
  const { user } = useAuth()
  const isAdmin = canAccessAdmin(user)
  const showDataMenu = canAccessDataCrud(user)
  const showAsignaciones = canManageAsignaciones(user)
  const showProgreso = canViewInvestigacionProgress(user)
  const [dimsOpen, setDimsOpen] = useState(false)
  const [invOpen, setInvOpen] = useState(true)
  const [factsOpen, setFactsOpen] = useState(false)
  const [securityOpen, setSecurityOpen] = useState(false)
  const [adminOpen, setAdminOpen] = useState(false)

  const dimensions = collections.filter((c) => c.group === 'dimension')
  const facts = collections.filter((c) => c.group === 'fact' || c.group === 'raw')

  const linkClass = ({ isActive }) =>
    `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
      isActive
        ? 'bg-brand-600 text-white shadow-sm shadow-brand-600/30'
        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
    }`

  return (
    <aside
      className={`flex h-screen flex-col border-r border-slate-200 bg-white transition-all duration-300 ${
        collapsed ? 'w-[72px]' : 'w-64'
      }`}
    >
      <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-5">
        {appIconUrl ? (
          <img
            src={appIconUrl}
            alt={appName}
            className="h-10 w-10 shrink-0 rounded-xl object-cover"
          />
        ) : (
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white">
            <Shield className="h-5 w-5" aria-hidden />
          </div>
        )}
        {!collapsed && (
          <div className="min-w-0">
            <p className="truncate text-sm font-bold text-slate-900">{appName}</p>
            <p className="truncate text-xs text-slate-500">{appSubtitle}</p>
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4" aria-label="Menú principal">
        <NavLink to="/" end className={linkClass}>
          <LayoutDashboard className="h-5 w-5 shrink-0" aria-hidden />
          {!collapsed && <span>Overview</span>}
        </NavLink>

        {!collapsed && (showAsignaciones || showProgreso) && (
          <>
            <button
              type="button"
              onClick={() => setInvOpen((o) => !o)}
              className="mt-6 flex w-full items-center justify-between px-3 text-xs font-semibold uppercase tracking-wider text-slate-400"
              aria-expanded={invOpen}
            >
              Investigaciones
              <ChevronDown
                className={`h-4 w-4 transition-transform ${invOpen ? '' : '-rotate-90'}`}
              />
            </button>
            {invOpen && (
              <ul className="mt-2 space-y-0.5">
                {showAsignaciones && (
                  <li>
                    <NavLink to="/investigaciones/asignar" className={linkClass}>
                      <UserCheck className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                      <span className="truncate">Asignar detective</span>
                    </NavLink>
                  </li>
                )}
                {showProgreso && (
                  <li>
                    <NavLink to="/investigaciones/progreso" className={linkClass}>
                      <ClipboardList className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                      <span className="truncate">
                        {showAsignaciones ? 'Progreso investigación' : 'Mis expedientes'}
                      </span>
                    </NavLink>
                  </li>
                )}
              </ul>
            )}
          </>
        )}

        {!collapsed && showDataMenu && (
          <>
            <button
              type="button"
              onClick={() => setDimsOpen((o) => !o)}
              className="mt-6 flex w-full items-center justify-between px-3 text-xs font-semibold uppercase tracking-wider text-slate-400"
              aria-expanded={dimsOpen}
            >
              Dimensiones
              <ChevronDown
                className={`h-4 w-4 transition-transform ${dimsOpen ? '' : '-rotate-90'}`}
              />
            </button>
            {dimsOpen && (
              <ul className="mt-2 space-y-0.5">
                {dimensions.map((c) => (
                  <li key={c.slug}>
                    <NavLink to={`/tabla/${c.slug}`} className={linkClass}>
                      <Table2 className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                      <span className="truncate">{c.label}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            )}

            <button
              type="button"
              onClick={() => setFactsOpen((o) => !o)}
              className="mt-6 flex w-full items-center justify-between px-3 text-xs font-semibold uppercase tracking-wider text-slate-400"
              aria-expanded={factsOpen}
            >
              Hechos / Raw
              <ChevronDown
                className={`h-4 w-4 transition-transform ${factsOpen ? '' : '-rotate-90'}`}
              />
            </button>
            {factsOpen && (
              <ul className="mt-2 space-y-0.5">
                {facts.map((c) => (
                  <li key={c.slug}>
                    <NavLink to={`/tabla/${c.slug}`} className={linkClass}>
                      {c.group === 'raw' ? (
                        <Database className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                      ) : (
                        <Shield className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                      )}
                      <span className="truncate">{c.label}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}

        {!collapsed && isAdmin && (
          <>
            <button
              type="button"
              onClick={() => setSecurityOpen((o) => !o)}
              className="mt-6 flex w-full items-center justify-between px-3 text-xs font-semibold uppercase tracking-wider text-slate-400"
              aria-expanded={securityOpen}
            >
              Seguridad
              <ChevronDown
                className={`h-4 w-4 transition-transform ${securityOpen ? '' : '-rotate-90'}`}
              />
            </button>
            {securityOpen && (
              <ul className="mt-2 space-y-0.5">
                <li>
                  <NavLink to="/seguridad/sesiones-activas" className={linkClass}>
                    <Monitor className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                    <span className="truncate">Sesiones activas</span>
                  </NavLink>
                </li>
              </ul>
            )}

            <button
              type="button"
              onClick={() => setAdminOpen((o) => !o)}
              className="mt-6 flex w-full items-center justify-between px-3 text-xs font-semibold uppercase tracking-wider text-slate-400"
              aria-expanded={adminOpen}
            >
              Administración
              <ChevronDown
                className={`h-4 w-4 transition-transform ${adminOpen ? '' : '-rotate-90'}`}
              />
            </button>
            {adminOpen && (
              <ul className="mt-2 space-y-0.5">
              <li>
                <NavLink to="/admin/usuarios" className={linkClass}>
                  <Users className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  <span className="truncate">Usuarios</span>
                </NavLink>
              </li>
              <li>
                <NavLink to="/admin/permisos" className={linkClass}>
                  <KeyRound className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  <span className="truncate">Permisos RBAC</span>
                </NavLink>
              </li>
              <li>
                <NavLink to="/admin/politicas" className={linkClass}>
                  <ShieldCheck className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  <span className="truncate">Políticas seguridad</span>
                </NavLink>
              </li>
              <li>
                <NavLink to="/admin/parametros" className={linkClass}>
                  <Settings className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  <span className="truncate">Parámetros</span>
                </NavLink>
              </li>
              <li>
                <NavLink to="/admin/respaldos" className={linkClass}>
                  <HardDrive className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  <span className="truncate">Respaldos</span>
                </NavLink>
              </li>
              <li>
                <NavLink to="/admin/catalogos" className={linkClass}>
                  <BookOpen className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  <span className="truncate">Catálogos delitos</span>
                </NavLink>
              </li>
              <li>
                <NavLink to="/admin/zonas" className={linkClass}>
                  <MapPin className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  <span className="truncate">Zonas geográficas</span>
                </NavLink>
              </li>
              <li>
                <NavLink to="/admin/estado-sistema" className={linkClass}>
                  <Activity className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  <span className="truncate">Estado del sistema</span>
                </NavLink>
              </li>
            </ul>
            )}
          </>
        )}

        <GenerateDataButton collapsed={collapsed} />
      </nav>

      <div className="border-t border-slate-100 p-3">
        <button
          type="button"
          onClick={onToggle}
          className="flex w-full items-center justify-center gap-2 rounded-xl py-2 text-sm text-slate-500 hover:bg-slate-100"
          aria-label={collapsed ? 'Expandir menú' : 'Colapsar menú'}
        >
          <ChevronLeft
            className={`h-5 w-5 transition-transform ${collapsed ? 'rotate-180' : ''}`}
          />
          {!collapsed && <span>Colapsar</span>}
        </button>
      </div>
    </aside>
  )
}

