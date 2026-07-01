import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Sun, Moon, LogOut, ChevronDown, KeyRound, UserRound } from 'lucide-react'
import BackupAlertsBell from './BackupAlertsBell'
import Breadcrumbs from './layout/Breadcrumbs'
import ChangePasswordModal from './ChangePasswordModal'
import UserAvatar from './UserAvatar'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

export default function Header() {
  const { user, logout, photoEpoch } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const [passwordModalOpen, setPasswordModalOpen] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    const handleOutside = (event) => {
      if (!menuRef.current?.contains(event.target)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleOutside)
    return () => document.removeEventListener('mousedown', handleOutside)
  }, [])

  const handleLogout = async () => {
    setMenuOpen(false)
    await logout()
    navigate('/login')
  }

  const openChangePassword = () => {
    setMenuOpen(false)
    setPasswordModalOpen(true)
  }

  return (
    <>
      <header className="topbar">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0">
            <Breadcrumbs />
          </div>

          <div className="flex items-center justify-end gap-2">
            <BackupAlertsBell />
            <button
              type="button"
              onClick={toggleTheme}
              className="rounded-2xl p-2.5 text-[#475569] transition hover:bg-white/80 hover:text-black"
              aria-label="Cambiar tema"
              title={theme === 'dark' ? 'Modo claro' : 'Modo oscuro'}
            >
              {theme === 'dark' ? (
                <Sun className="h-[18px] w-[18px]" />
              ) : (
                <Moon className="h-[18px] w-[18px]" />
              )}
            </button>
            <div className="profile-card relative" ref={menuRef}>
              <div className="profile-avatar overflow-hidden">
                <UserAvatar
                  key={`${user?.id_usuario}-${user?.foto_actualizada_en || ''}-${photoEpoch}`}
                  user={user}
                  className="h-full w-full"
                  textClassName="text-xs"
                  photoVersion={user?.foto_actualizada_en || String(photoEpoch)}
                />
              </div>
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
                onClick={() => setMenuOpen((prev) => !prev)}
                className="ml-1 rounded-xl p-2 text-[#475569] transition hover:bg-white hover:text-black"
                aria-label="Menú de cuenta"
                aria-expanded={menuOpen}
                aria-haspopup="menu"
              >
                <ChevronDown
                  className={`h-4 w-4 transition-transform ${menuOpen ? 'rotate-180' : ''}`}
                />
              </button>
              {menuOpen && (
                <ul
                  role="menu"
                  className="absolute right-0 top-full z-50 mt-2 min-w-[12rem] overflow-hidden rounded-xl border border-slate-200/80 bg-white py-1 shadow-lg"
                >
                  <li role="none">
                    <Link
                      to="/perfil"
                      role="menuitem"
                      onClick={() => setMenuOpen(false)}
                      className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm text-slate-700 transition hover:bg-slate-50"
                    >
                      <UserRound className="h-4 w-4 text-slate-500" />
                      Perfil
                    </Link>
                  </li>
                  <li role="none">
                    <button
                      type="button"
                      role="menuitem"
                      onClick={openChangePassword}
                      className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm text-slate-700 transition hover:bg-slate-50"
                    >
                      <KeyRound className="h-4 w-4 text-slate-500" />
                      Cambiar contraseña
                    </button>
                  </li>
                  <li role="none" className="my-1 border-t border-slate-100" />
                  <li role="none">
                    <button
                      type="button"
                      role="menuitem"
                      onClick={handleLogout}
                      className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm text-red-600 transition hover:bg-red-50"
                    >
                      <LogOut className="h-4 w-4" />
                      Cerrar sesión
                    </button>
                  </li>
                </ul>
              )}
            </div>
          </div>
        </div>
      </header>

      <ChangePasswordModal open={passwordModalOpen} onClose={() => setPasswordModalOpen(false)} />
    </>
  )
}
