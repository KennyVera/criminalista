import { useAuth } from '../../context/AuthContext'
import { Card } from '../ui'

export default function AdminGuard({ children }) {
  const { user } = useAuth()
  if (user?.nombre_rol?.toLowerCase() !== 'admin') {
    return (
      <Card className="border-amber-200 bg-amber-50">
        <p className="font-medium text-amber-900">Solo Administrador</p>
        <p className="mt-1 text-sm text-amber-800">
          El paquete Administración del Sistema requiere rol Admin.
        </p>
      </Card>
    )
  }
  return children
}
