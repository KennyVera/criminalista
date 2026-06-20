import { AlertTriangle, Wrench } from 'lucide-react'
import { Card } from '../components/ui'

export default function MaintenancePage({ message }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6 dark:bg-slate-950">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgb(99_102_241/0.1),transparent)]" />
      <Card className="relative w-full max-w-md p-8 text-center shadow-[var(--shadow-elevated)]">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-50 text-amber-700 ring-1 ring-amber-200 dark:bg-amber-950/50 dark:text-amber-300 dark:ring-amber-800">
          <Wrench className="h-8 w-8" />
        </div>
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50">Sistema en mantenimiento</h1>
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
          {message ||
            'Estamos realizando tareas de recuperación de datos. Intente más tarde o contacte al administrador.'}
        </p>
        <div className="alert-banner alert-banner--warning mt-6 text-left text-xs">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>
            Si usted es personal operativo, no es necesario iniciar sesión hasta que el
            administrador restaure el sistema.
          </span>
        </div>
      </Card>
    </div>
  )
}
