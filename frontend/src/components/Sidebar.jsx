import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  ChevronDown,
  PanelLeftClose,
  Monitor,
  Users,
  KeyRound,
  Settings,
  HardDrive,
  BookOpen,
  MapPin,
  Activity,
  UserCheck,
  ClipboardList,
  Briefcase,
  ShieldCheck,
  Table2,
  Database,
  Shield,
  Sparkles,
  FileText,
  Radio,
  Navigation,
} from 'lucide-react'
import GenerateDataButton from './GenerateDataButton'
import BrandLogo from './layout/BrandLogo'
import { useAuth } from '../context/AuthContext'
import { cn } from '../lib/cn'
import {
  canAccessAdmin,
  canAccessDataCrud,
  canManageAsignaciones,
  canViewInvestigacionProgress,
  canViewDashboard,
  canViewOperationalIndicators,
  canManagePatrullas,
  canDespachar,
  isOficial,
} from '../utils/roles'

function NavSection({ title, open, onToggle, collapsed, children }) {
  if (collapsed) return <ul className="mt-0.5 space-y-0.5">{children}</ul>
  return (
    <div>
      <button
        type="button"
        onClick={onToggle}
        className="nav-section-label flex w-full items-center justify-between"
        aria-expanded={open}
      >
        {title}
        <ChevronDown className={cn('h-3 w-3 transition-transform', !open && '-rotate-90')} />
      </button>
      {open && <ul className="mt-0.5 space-y-0.5">{children}</ul>}
    </div>
  )
}

export default function Sidebar({
  collections,
  collapsed,
  onToggle,
  appSubtitle = 'Panel de analítica criminal',
  appIconUrl = '',
}) {
  const { user } = useAuth()
  const isAdmin = canAccessAdmin(user)
  const showDataMenu = canAccessDataCrud(user)
  const showDashboard = canViewDashboard(user)
  const showPrediccion = canViewOperationalIndicators(user)
  const showAsignaciones = canManageAsignaciones(user)
  const showProgreso = canViewInvestigacionProgress(user)
  const showPatrullas = canManagePatrullas(user)
  const showDespacho = canDespachar(user)
  const showMisPatrullas = isOficial(user)
  const showOperaciones = showPatrullas || showDespacho || showMisPatrullas
  const [invOpen, setInvOpen] = useState(false)
  const [opsOpen, setOpsOpen] = useState(false)
  const [tablesOpen, setTablesOpen] = useState(false)
  const [securityOpen, setSecurityOpen] = useState(false)
  const [adminOpen, setAdminOpen] = useState(false)
  const [adminMoreOpen, setAdminMoreOpen] = useState(false)

  const dimensions = collections.filter((c) => c.group === 'dimension')
  const facts = collections.filter((c) => c.group === 'fact' || c.group === 'raw')

  const linkClass = ({ isActive }) =>
    cn('nav-link', isActive && 'nav-link--active', collapsed && 'justify-center px-2')

  return (
    <aside className={cn('sidebar-shell', collapsed ? 'w-[72px]' : 'w-[272px]')}>
      <div className="flex items-center gap-3 px-5 py-5">
        {appIconUrl ? (
          <img
            src={appIconUrl}
            alt="CrimeTrack"
            className="h-9 w-9 shrink-0 rounded-lg object-cover"
          />
        ) : (
          <BrandLogo />
        )}
        {!collapsed && (
          <div className="min-w-0">
            <p className="sidebar-brand-line">
              CRIMETRACK <span className="sidebar-brand-line--light">ANALYTICS</span>
            </p>
            <p className="sidebar-brand-sub truncate">{appSubtitle}</p>
          </div>
        )}
      </div>

      <div className="sidebar-divider" />

      <nav className="flex-1 overflow-y-auto px-1 py-2" aria-label="Menú principal">
        {!collapsed && <p className="nav-section-label">Menú</p>}
        {showDashboard && (
          <NavLink to="/" end className={linkClass} title={collapsed ? 'Panel de control' : undefined}>
            <LayoutDashboard className="h-[18px] w-[18px] shrink-0" aria-hidden />
            {!collapsed && <span>Panel de control</span>}
          </NavLink>
        )}
        {showPrediccion && (
          <NavLink
            to="/analitica/prediccion"
            className={linkClass}
            title={collapsed ? 'Predicción criminal' : undefined}
          >
            <Sparkles className="h-[18px] w-[18px] shrink-0" aria-hidden />
            {!collapsed && <span>Predicción criminal</span>}
          </NavLink>
        )}
        {showPrediccion && (
          <NavLink
            to="/reportes"
            className={linkClass}
            title={collapsed ? 'Reportes' : undefined}
          >
            <FileText className="h-[18px] w-[18px] shrink-0" aria-hidden />
            {!collapsed && <span>Reportes</span>}
          </NavLink>
        )}

        {(showAsignaciones || showProgreso) && (
          <NavSection
            title="Investigaciones"
            open={invOpen}
            onToggle={() => setInvOpen((o) => !o)}
            collapsed={collapsed}
          >
            {showAsignaciones && (
              <li>
                <NavLink to="/investigaciones/asignar" className={linkClass}>
                  <UserCheck className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  {!collapsed && <span className="truncate">Asignar detective</span>}
                </NavLink>
              </li>
            )}
            {showProgreso && (
              <li>
                <NavLink to="/investigaciones/progreso" className={linkClass}>
                  <ClipboardList className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  {!collapsed && <span className="truncate">Progreso investigación</span>}
                </NavLink>
              </li>
            )}
            {showProgreso && (
              <li>
                <NavLink to="/tabla/dim_caso" className={linkClass}>
                  <Briefcase className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  {!collapsed && <span className="truncate">Casos</span>}
                </NavLink>
              </li>
            )}
          </NavSection>
        )}

        {showOperaciones && (
          <NavSection
            title="Operaciones de patrulla"
            open={opsOpen}
            onToggle={() => setOpsOpen((o) => !o)}
            collapsed={collapsed}
          >
            {showPatrullas && (
              <li>
                <NavLink to="/operaciones/patrullas" className={linkClass}>
                  <ShieldCheck className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  {!collapsed && <span className="truncate">Patrullas</span>}
                </NavLink>
              </li>
            )}
            {showDespacho && (
              <li>
                <NavLink to="/operaciones/despacho" className={linkClass}>
                  <Radio className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  {!collapsed && <span className="truncate">Central de despacho</span>}
                </NavLink>
              </li>
            )}
            {showMisPatrullas && (
              <li>
                <NavLink to="/operaciones/mis-patrullas" className={linkClass}>
                  <Navigation className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  {!collapsed && <span className="truncate">Mis patrullas</span>}
                </NavLink>
              </li>
            )}
          </NavSection>
        )}

        {showDataMenu && !collapsed && (
          <NavSection
            title="Explorar tablas"
            open={tablesOpen}
            onToggle={() => setTablesOpen((o) => !o)}
            collapsed={collapsed}
          >
            {dimensions.map((c) => (
              <li key={c.slug}>
                <NavLink to={`/tabla/${c.slug}`} className={linkClass}>
                  <Table2 className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  <span className="truncate">{c.label}</span>
                </NavLink>
              </li>
            ))}
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
          </NavSection>
        )}

        {isAdmin && (
          <>
            <NavSection
              title="Seguridad"
              open={securityOpen}
              onToggle={() => setSecurityOpen((o) => !o)}
              collapsed={collapsed}
            >
              <li>
                <NavLink to="/seguridad/sesiones-activas" className={linkClass}>
                  <Monitor className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  {!collapsed && <span className="truncate">Sesiones activas</span>}
                </NavLink>
              </li>
              <li>
                <NavLink to="/seguridad/auditoria" className={linkClass}>
                  <ShieldCheck className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  {!collapsed && <span className="truncate">Auditoría</span>}
                </NavLink>
              </li>
            </NavSection>

            <NavSection
              title="Administración"
              open={adminOpen}
              onToggle={() => setAdminOpen((o) => !o)}
              collapsed={collapsed}
            >
              <li>
                <NavLink to="/admin/usuarios" className={linkClass}>
                  <Users className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  {!collapsed && <span className="truncate">Usuarios</span>}
                </NavLink>
              </li>
              <li>
                <NavLink to="/admin/permisos" className={linkClass}>
                  <KeyRound className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                  {!collapsed && <span className="truncate">Roles y permisos</span>}
                </NavLink>
              </li>
              {!collapsed && (
                <li>
                  <button
                    type="button"
                    onClick={() => setAdminMoreOpen((o) => !o)}
                    className="nav-link w-full"
                  >
                    <Settings className="h-4 w-4 shrink-0 opacity-70" />
                    <span className="flex-1 truncate text-left">Más opciones</span>
                    <ChevronDown
                      className={cn('h-3 w-3', !adminMoreOpen && '-rotate-90')}
                    />
                  </button>
                </li>
              )}
              {adminMoreOpen && !collapsed && (
                <>
                  <li>
                    <NavLink to="/admin/parametros" className={linkClass}>
                      <Settings className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                      <span className="truncate">Parámetros</span>
                    </NavLink>
                  </li>
                  <li>
                    <NavLink to="/admin/politicas" className={linkClass}>
                      <ShieldCheck className="h-4 w-4 shrink-0 opacity-70" aria-hidden />
                      <span className="truncate">Políticas de seguridad</span>
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
                </>
              )}
            </NavSection>
          </>
        )}

        <GenerateDataButton collapsed={collapsed} />
      </nav>

      <div className="sidebar-divider" />
      <div className="p-3">
        <button
          type="button"
          onClick={onToggle}
          className="flex w-full items-center justify-center gap-2 rounded-2xl py-2.5 text-xs font-medium text-[#64748B] transition hover:bg-white/80 hover:text-[#0F172A]"
          aria-label={collapsed ? 'Expandir menú' : 'Colapsar menú'}
        >
          <PanelLeftClose
            className={cn('h-4 w-4 transition-transform', collapsed && 'rotate-180')}
          />
          {!collapsed && <span>Colapsar menú</span>}
        </button>
      </div>
    </aside>
  )
}
