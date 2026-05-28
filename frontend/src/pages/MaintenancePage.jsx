import { AlertTriangle, Wrench } from 'lucide-react'
import { Card } from '../components/ui'

export default function MaintenancePage({ message }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 p-6">
      <Card className="max-w-md w-full p-8 text-center shadow-xl">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-100 text-amber-700">
          <Wrench className="h-8 w-8" />
        </div>
        <h1 className="text-xl font-bold text-slate-900">Sistema en mantenimiento</h1>
        <p className="mt-3 text-sm text-slate-600">
          {message ||
            'Estamos realizando tareas de recuperación de datos. Intente más tarde o contacte al administrador.'}
        </p>
        <div className="mt-6 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-left text-xs text-amber-900">
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
