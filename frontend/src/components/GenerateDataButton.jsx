import { NavLink } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import { cn } from '../lib/cn'

export default function GenerateDataButton({ collapsed }) {
  return (
    <NavLink
      to="/generar-datos"
      title="Generar datos Faker"
      className={({ isActive }) =>
        cn('sidebar-cta', isActive && 'sidebar-cta--active', collapsed && 'px-2')
      }
    >
      <Sparkles className="h-4 w-4 shrink-0" aria-hidden />
      {!collapsed && <span>Generar datos (Faker)</span>}
    </NavLink>
  )
}
