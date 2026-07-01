import { NavLink } from 'react-router-dom'
import { RefreshCw } from 'lucide-react'
import { cn } from '../lib/cn'

export default function GenerateDataButton({ collapsed }) {
  return (
    <NavLink
      to="/generar-datos"
      title="Sincronizar datos desde PocketBase"
      className={({ isActive }) =>
        cn('sidebar-cta', isActive && 'sidebar-cta--active', collapsed && 'px-2')
      }
    >
      <RefreshCw className="h-4 w-4 shrink-0" aria-hidden />
      {!collapsed && <span>Sincronizar datos</span>}
    </NavLink>
  )
}
