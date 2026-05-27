import { useEffect, useState } from 'react'
import { KeyRound } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Button, Card, Spinner } from '../../components/ui'
import { useToast } from '../../context/ToastContext'

export default function AdminPermissionsPage() {
  const [roles, setRoles] = useState([])
  const [permisos, setPermisos] = useState([])
  const [fkRol, setFkRol] = useState(1)
  const [selected, setSelected] = useState([])
  const [loading, setLoading] = useState(true)
  const toast = useToast()

  useEffect(() => {
    Promise.all([adminApi.roles(), adminApi.permisos()]).then(([r, p]) => {
      setRoles(r.items || [])
      setPermisos(p.items || [])
      setLoading(false)
    })
  }, [])

  useEffect(() => {
    if (!fkRol) return
    adminApi.rolPermisos(fkRol).then((d) => setSelected(d.codigos || []))
  }, [fkRol])

  const save = async () => {
    try {
      await adminApi.setRolPermisos(fkRol, selected)
      toast.success('Éxito', 'Permisos del rol actualizados')
    } catch (e) {
      toast.error('Error', e.message)
    }
  }

  return (
    <AdminGuard>
      <AdminPageHeader
        title="Gestionar permisos (RBAC)"
        subtitle="Control de acceso por rol — incluido en políticas de seguridad"
        icon={KeyRound}
      />
      <Card>
        {loading ? (
          <Spinner />
        ) : (
          <div className="space-y-4">
            <label className="block max-w-xs">
              <span className="text-sm font-medium">Rol</span>
              <select
                value={fkRol}
                onChange={(e) => setFkRol(Number(e.target.value))}
                className="mt-1 w-full rounded-xl border px-3 py-2 text-sm"
              >
                {roles.map((r) => (
                  <option key={r.id_rol} value={r.id_rol}>
                    {r.nombre_rol}
                  </option>
                ))}
              </select>
            </label>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {permisos.map((p) => (
                <label
                  key={p.codigo}
                  className="flex items-start gap-2 rounded-lg border p-3 text-sm"
                >
                  <input
                    type="checkbox"
                    checked={selected.includes(p.codigo)}
                    onChange={() =>
                      setSelected((s) =>
                        s.includes(p.codigo) ? s.filter((c) => c !== p.codigo) : [...s, p.codigo]
                      )
                    }
                  />
                  <span>
                    <strong>{p.nombre}</strong>
                    <br />
                    <span className="text-xs text-slate-500">{p.modulo}</span>
                  </span>
                </label>
              ))}
            </div>
            <Button type="button" onClick={save}>
              Guardar permisos del rol
            </Button>
          </div>
        )}
      </Card>
    </AdminGuard>
  )
}
