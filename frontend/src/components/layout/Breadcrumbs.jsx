import { Link, useLocation } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'
import { cn } from '../../lib/cn'

const LABELS = {
  '': 'Panel de control',
  tabla: 'Gestión de datos',
  investigaciones: 'Investigaciones',
  asignar: 'Asignar detective',
  progreso: 'Progreso operativo',
  expedientes: 'Expediente',
  seguridad: 'Seguridad',
  'sesiones-activas': 'Sesiones activas',
  admin: 'Administración',
  usuarios: 'Usuarios',
  permisos: 'Permisos',
  politicas: 'Políticas',
  parametros: 'Parámetros',
  respaldos: 'Respaldos',
  catalogos: 'Catálogos',
  zonas: 'Zonas',
  'estado-sistema': 'Estado del sistema',
  'generar-datos': 'Generación de datos',
}

export default function Breadcrumbs({ className }) {
  const { pathname } = useLocation()
  const segments = pathname.split('/').filter(Boolean)

  const crumbs = segments.map((seg, i) => {
    const path = `/${segments.slice(0, i + 1).join('/')}`
    const isLast = i === segments.length - 1
    const label = LABELS[seg] || decodeURIComponent(seg)
    return { path, label, isLast }
  })

  if (crumbs.length === 0) {
    return (
      <nav aria-label="Breadcrumb" className={cn('flex items-center gap-2 text-sm', className)}>
        <span className="font-bold text-black">Panel de control</span>
      </nav>
    )
  }

  return (
    <nav
      aria-label="Breadcrumb"
      className={cn('flex flex-wrap items-center gap-2 text-sm', className)}
    >
      <Link
        to="/"
        className="flex items-center gap-1.5 text-[#64748B] transition hover:text-[#6366F1]"
      >
        <Home className="h-3.5 w-3.5" />
        <span className="sr-only sm:not-sr-only">Inicio</span>
      </Link>
      {crumbs.map((c) => (
        <span key={c.path} className="flex items-center gap-2">
          <ChevronRight className="h-3.5 w-3.5 text-[#CBD5E1]" />
          {c.isLast ? (
            <span className="font-bold text-black">{c.label}</span>
          ) : (
            <Link to={c.path} className="text-[#64748B] transition hover:text-[#6366F1]">
              {c.label}
            </Link>
          )}
        </span>
      ))}
    </nav>
  )
}
