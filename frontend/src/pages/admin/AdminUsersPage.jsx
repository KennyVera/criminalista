import { useCallback, useEffect, useState } from 'react'
import { UserPlus, Pencil, Trash2, UserCheck, UserX } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Button, Card, Badge, Spinner, PasswordInput } from '../../components/ui'
import { useToast } from '../../context/ToastContext'

const emptyForm = {
  nombres: '',
  apellidos: '',
  email: '',
  numero_placa: '',
  fk_rol: 4,
  password: '',
  estado_cuenta: 'Activa',
}

export default function AdminUsersPage() {
  const [items, setItems] = useState([])
  const [roles, setRoles] = useState([])
  const [permisos, setPermisos] = useState([])
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [selectedPerms, setSelectedPerms] = useState([])
  const toast = useToast()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [u, r, p] = await Promise.all([adminApi.users(), adminApi.roles(), adminApi.permisos()])
      setItems(u.items || [])
      setRoles(r.items || [])
      setPermisos(p.items || [])
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const openCreate = () => {
    setEditing(null)
    setForm(emptyForm)
    setSelectedPerms([])
    setFormOpen(true)
  }

  const openEdit = async (user) => {
    setEditing(user)
    setForm({
      nombres: user.nombres,
      apellidos: user.apellidos,
      email: user.email,
      numero_placa: user.numero_placa,
      fk_rol: user.fk_rol,
      password: '',
      estado_cuenta: user.estado_cuenta,
    })
    const rp = await adminApi.rolPermisos(user.fk_rol)
    setSelectedPerms(rp.codigos || [])
    setFormOpen(true)
  }

  const save = async (e) => {
    e.preventDefault()
    try {
      const body = { ...form, fk_rol: Number(form.fk_rol), permisos: selectedPerms }
      if (editing) {
        if (!body.password) delete body.password
        await adminApi.updateUser(editing.id_usuario, body)
        toast.success('Éxito', 'Usuario actualizado correctamente')
      } else {
        await adminApi.createUser(body)
        toast.success('Éxito', 'Usuario registrado correctamente')
      }
      setFormOpen(false)
      load()
    } catch (err) {
      toast.error('Error', err.message)
    }
  }

  const togglePerm = (code) => {
    setSelectedPerms((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    )
  }

  return (
    <AdminGuard>
      <AdminPageHeader
        title="Registrar y editar usuarios"
        subtitle="Incluye asignar roles y gestionar permisos (diagrama Administración)"
        icon={UserPlus}
      >
        <Button type="button" onClick={openCreate}>
          <UserPlus className="h-4 w-4" />
          Registrar usuario
        </Button>
      </AdminPageHeader>

      {formOpen && (
        <Card className="mb-6 border-brand-200">
          <form onSubmit={save} className="space-y-4">
            <h3 className="font-semibold">{editing ? 'Editar usuario' : 'Nuevo usuario'}</h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <input
                placeholder="Nombres"
                value={form.nombres}
                onChange={(e) => setForm({ ...form, nombres: e.target.value })}
                className="rounded-xl border px-3 py-2 text-sm"
                required
              />
              <input
                placeholder="Apellidos"
                value={form.apellidos}
                onChange={(e) => setForm({ ...form, apellidos: e.target.value })}
                className="rounded-xl border px-3 py-2 text-sm"
                required
              />
              <input
                type="email"
                placeholder="Email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="rounded-xl border px-3 py-2 text-sm"
                required
              />
              <input
                placeholder="Número placa"
                value={form.numero_placa}
                onChange={(e) => setForm({ ...form, numero_placa: e.target.value })}
                className="rounded-xl border px-3 py-2 text-sm"
                required
              />
              <select
                value={form.fk_rol}
                onChange={(e) => setForm({ ...form, fk_rol: e.target.value })}
                className="rounded-xl border px-3 py-2 text-sm"
              >
                {roles.map((r) => (
                  <option key={r.id_rol} value={r.id_rol}>
                    {r.nombre_rol}
                  </option>
                ))}
              </select>
              <PasswordInput
                placeholder={editing ? 'Nueva contraseña (opcional)' : 'Contraseña'}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                inputClassName="rounded-xl border px-3 py-2 text-sm"
                required={!editing}
                autoComplete={editing ? 'new-password' : 'new-password'}
              />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-slate-700">Gestionar permisos</p>
              <div className="grid max-h-40 gap-2 overflow-y-auto sm:grid-cols-2">
                {permisos.map((p) => (
                  <label key={p.codigo} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={selectedPerms.includes(p.codigo)}
                      onChange={() => togglePerm(p.codigo)}
                    />
                    {p.nombre}
                  </label>
                ))}
              </div>
            </div>
            <div className="flex gap-2">
              <Button type="submit">Guardar</Button>
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>
                Cancelar
              </Button>
            </div>
          </form>
        </Card>
      )}

      <Card>
        {loading ? (
          <div className="flex justify-center py-12">
            <Spinner />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[800px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-3 py-2">Usuario</th>
                  <th className="px-3 py-2">Rol</th>
                  <th className="px-3 py-2">Placa</th>
                  <th className="px-3 py-2">Estado</th>
                  <th className="px-3 py-2">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {items.map((u) => (
                  <tr key={u.id_usuario} className="border-t">
                    <td className="px-3 py-2">
                      <p className="font-medium">
                        {u.nombres} {u.apellidos}
                      </p>
                      <p className="text-xs text-slate-500">{u.email}</p>
                    </td>
                    <td className="px-3 py-2">{u.nombre_rol}</td>
                    <td className="px-3 py-2">{u.numero_placa}</td>
                    <td className="px-3 py-2">
                      <Badge
                        tone={
                          u.estado_cuenta === 'Activa'
                            ? 'green'
                            : u.estado_cuenta === 'Bloqueada'
                              ? 'red'
                              : 'slate'
                        }
                      >
                        {u.estado_cuenta}
                        {u.intentos_login_fallidos > 0 && u.estado_cuenta === 'Activa' && (
                          <span className="ml-1 text-xs opacity-80">
                            ({u.intentos_login_fallidos} fallos)
                          </span>
                        )}
                      </Badge>
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex gap-1">
                        <button
                          type="button"
                          className="rounded-lg p-2 hover:bg-slate-100"
                          onClick={() => openEdit(u)}
                          title="Editar"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          className="rounded-lg p-2 hover:bg-slate-100"
                          onClick={async () => {
                            try {
                              const activa = u.estado_cuenta !== 'Activa'
                              await adminApi.setUserStatus(u.id_usuario, activa)
                              toast.success(
                                'Éxito',
                                activa ? 'Cuenta activada' : 'Cuenta desactivada'
                              )
                              load()
                            } catch (e) {
                              toast.error('Error', e.message)
                            }
                          }}
                          title="Activar/desactivar"
                        >
                          {u.estado_cuenta === 'Activa' ? (
                            <UserX className="h-4 w-4 text-amber-600" />
                          ) : (
                            <UserCheck className="h-4 w-4 text-emerald-600" />
                          )}
                        </button>
                        {u.id_usuario !== 1 && (
                          <button
                            type="button"
                            className="rounded-lg p-2 hover:bg-red-50"
                            onClick={async () => {
                              if (!confirm('¿Eliminar usuario?')) return
                              try {
                                await adminApi.deleteUser(u.id_usuario)
                                toast.success('Éxito', 'Usuario eliminado')
                                load()
                              } catch (e) {
                                toast.error('Error', e.message)
                              }
                            }}
                            title="Eliminar"
                          >
                            <Trash2 className="h-4 w-4 text-red-600" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </AdminGuard>
  )
}
