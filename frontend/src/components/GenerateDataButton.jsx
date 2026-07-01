import { NavLink } from 'react-router-dom'
import { Workflow } from 'lucide-react'
import { cn } from '../lib/cn'

export default function GenerateDataButton({ collapsed }) {
  return (
    <NavLink
      to="/generar-datos"
      title="Ejecutar proceso ETL desde PocketBase"
      className={({ isActive }) =>
        cn('sidebar-cta', isActive && 'sidebar-cta--active', collapsed && 'px-2')
      }
    >
      <Workflow className="h-4 w-4 shrink-0" aria-hidden />
      {!collapsed && <span>Ejecutar ETL</span>}
    </NavLink>
  )
}
