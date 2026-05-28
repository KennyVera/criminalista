import { Sun, Moon, LogOut } from 'lucide-react'
import BackupAlertsBell from './BackupAlertsBell'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

export default function Header({ title, subtitle }) {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()

  const initials =
    user?.nombres && user?.apellidos
      ? `${user.nombres[0]}${user.apellidos[0]}`.toUpperCase()
      : 'CT'
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200/80 bg-white/80 px-6 py-4 backdrop-blur-sm">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-900">{title}</h1>
        {subtitle && (
          <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>
        )}
      </div>
      <div className="flex items-center gap-3">
        <BackupAlertsBell />
        <button
          type="button"
          onClick={toggleTheme}
          className="rounded-xl p-2.5 text-slate-500 hover:bg-slate-100"
          aria-label="Cambiar tema"
          title={theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
        >
          {theme === 'dark' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
        </button>
        <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-600 text-sm font-semibold text-white">
            {initials}
          </div>
          <div className="hidden sm:block text-left">
            <p className="text-sm font-semibold text-slate-800">
              {user ? `${user.nombres} ${user.apellidos}` : 'Usuario'}
            </p>
            <p className="text-xs text-slate-500">
              {user?.nombre_rol || '—'} · {user?.numero_placa || ''}
            </p>
          </div>
          <button
            type="button"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-200"
            aria-label="Cerrar sesión"
            onClick={async () => {
              await logout()
              navigate('/login')
            }}
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  )
}

