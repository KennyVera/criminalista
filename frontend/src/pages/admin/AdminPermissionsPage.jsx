import { useEffect, useState } from 'react'
import { KeyRound } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Button, Card, Badge, Spinner } from '../../components/ui'
import { useToast } from '../../context/ToastContext'

const SELECT =
  'mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2.5 text-sm text-slate-900 transition focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-100'

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

  const currentRole = roles.find((r) => r.id_rol === fkRol)

  return (
    <AdminGuard>
      <AdminPageHeader
        title="Gestionar permisos (RBAC)"
        subtitle="Control de acceso por rol — incluido en políticas de seguridad"
        icon={KeyRound}
      />
      <Card>
        {loading ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex flex-wrap items-end justify-between gap-4 border-b border-slate-100 pb-5">
              <label className="block min-w-[220px] flex-1 max-w-xs">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Rol
                </span>
                <select value={fkRol} onChange={(e) => setFkRol(Number(e.target.value))} className={SELECT}>
                  {roles.map((r) => (
                    <option key={r.id_rol} value={r.id_rol}>
                      {r.nombre_rol}
                    </option>
                  ))}
                </select>
              </label>
              <div className="flex items-center gap-3">
                {currentRole && (
                  <Badge tone="blue">
                    {selected.length} / {permisos.length} permisos
                  </Badge>
                )}
                <Button type="button" onClick={save}>
                  Guardar permisos del rol
                </Button>
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {permisos.map((p) => {
                const checked = selected.includes(p.codigo)
                return (
                  <label
                    key={p.codigo}
                    className={`flex cursor-pointer items-start gap-3 rounded-xl border p-4 text-sm transition ${
                      checked
                        ? 'border-brand-200 bg-brand-50/50 shadow-sm'
                        : 'border-slate-200 bg-slate-50/30 hover:border-slate-300 hover:bg-white'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() =>
                        setSelected((s) =>
                          s.includes(p.codigo) ? s.filter((c) => c !== p.codigo) : [...s, p.codigo]
                        )
                      }
                      className="mt-0.5 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                    />
                    <span>
                      <strong className="text-slate-900">{p.nombre}</strong>
                      <br />
                      <span className="text-xs text-slate-500">{p.modulo}</span>
                    </span>
                  </label>
                )
              })}
            </div>
          </div>
        )}
      </Card>
    </AdminGuard>
  )
}
