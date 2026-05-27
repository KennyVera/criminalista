import { NavLink } from 'react-router-dom'
import { Sparkles } from 'lucide-react'

export default function GenerateDataButton({ collapsed }) {
  const linkClass = ({ isActive }) =>
    `mt-4 flex w-full items-center justify-center gap-2 rounded-xl border px-3 py-2.5 text-sm font-medium transition-colors ${
      isActive
        ? 'border-brand-600 bg-brand-600 text-white shadow-sm'
        : 'border-brand-200 bg-brand-50 text-brand-700 hover:bg-brand-100'
    }`

  return (
    <NavLink to="/generar-datos" className={linkClass} title="Generar datos Faker">
      <Sparkles className="h-4 w-4 shrink-0" aria-hidden />
      {!collapsed && <span>Generar datos (Faker)</span>}
    </NavLink>
  )
}
