import { Sun, Moon, Search, LogOut } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import BackupAlertsBell from './BackupAlertsBell'
import Breadcrumbs from './layout/Breadcrumbs'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

export default function Header() {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()

  const initials =
    user?.nombres && user?.apellidos
      ? `${user.nombres[0]}${user.apellidos[0]}`.toUpperCase()
      : 'CT'

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <header className="topbar">
      <div className="grid grid-cols-1 items-center gap-4 lg:grid-cols-[1fr_minmax(0,28rem)_1fr]">
        <div className="min-w-0 lg:justify-self-start">
          <Breadcrumbs />
        </div>

        <div className="relative hidden justify-self-center lg:block">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#64748B]" />
          <input
            type="search"
            className="topbar-search"
            placeholder="Buscar expedientes, casos, usuarios…"
            aria-label="Búsqueda global"
          />
          <kbd className="pointer-events-none absolute right-3 top-1/2 hidden -translate-y-1/2 rounded-lg border border-slate-200/80 bg-white/90 px-2 py-0.5 font-mono text-[10px] font-medium text-[#64748B] sm:inline">
            ⌘ K
          </kbd>
        </div>

        <div className="flex items-center justify-end gap-2 lg:justify-self-end">
          <BackupAlertsBell />
          <button
            type="button"
            onClick={toggleTheme}
            className="rounded-2xl p-2.5 text-[#475569] transition hover:bg-white/80 hover:text-black"
            aria-label="Cambiar tema"
            title={theme === 'dark' ? 'Modo claro' : 'Modo oscuro'}
          >
            {theme === 'dark' ? <Sun className="h-[18px] w-[18px]" /> : <Moon className="h-[18px] w-[18px]" />}
          </button>
          <div className="profile-card">
            <div className="profile-avatar">{initials}</div>
            <div className="hidden text-left sm:block">
              <p className="text-sm font-bold leading-tight text-black">
                {user ? `${user.nombres} ${user.apellidos}` : 'Usuario'}
              </p>
              <p className="text-[11px] font-semibold text-[#475569]">
                {user?.nombre_rol || '—'}
                {user?.numero_placa ? ` · ${user.numero_placa}` : ''}
              </p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="ml-1 rounded-xl p-2 text-[#475569] transition hover:bg-red-50 hover:text-[#EF4444]"
              aria-label="Cerrar sesión"
              title="Cerrar sesión"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
