import { useCallback, useEffect, useState } from 'react'
import { UserPlus, Pencil, Trash2, UserCheck, UserX } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Button, Card, Badge, Spinner, PasswordInput } from '../../components/ui'
import { useToast } from '../../context/ToastContext'

const INPUT =
  'w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 transition focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-100'

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
        <Card className="mb-6 border-brand-200/60 bg-gradient-to-br from-brand-50/40 to-white">
          <form onSubmit={save} className="space-y-5">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
              <h3 className="text-base font-semibold text-slate-900">
                {editing ? 'Editar usuario' : 'Nuevo usuario'}
              </h3>
              {editing && <Badge tone="blue">ID {editing.id_usuario}</Badge>}
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <input
                placeholder="Nombres"
                value={form.nombres}
                onChange={(e) => setForm({ ...form, nombres: e.target.value })}
                className={INPUT}
                required
              />
              <input
                placeholder="Apellidos"
                value={form.apellidos}
                onChange={(e) => setForm({ ...form, apellidos: e.target.value })}
                className={INPUT}
                required
              />
              <input
                type="email"
                placeholder="Email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className={INPUT}
                required
              />
              <input
                placeholder="Número placa"
                value={form.numero_placa}
                onChange={(e) => setForm({ ...form, numero_placa: e.target.value })}
                className={INPUT}
                required
              />
              <select
                value={form.fk_rol}
                onChange={(e) => setForm({ ...form, fk_rol: e.target.value })}
                className={INPUT}
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
                inputClassName="bg-slate-50/50"
                required={!editing}
                autoComplete={editing ? 'new-password' : 'new-password'}
              />
            </div>
            <div>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Gestionar permisos
              </p>
              <div className="grid max-h-44 gap-2 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50/50 p-3 sm:grid-cols-2">
                {permisos.map((p) => (
                  <label
                    key={p.codigo}
                    className="flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm transition hover:bg-white"
                  >
                    <input
                      type="checkbox"
                      checked={selectedPerms.includes(p.codigo)}
                      onChange={() => togglePerm(p.codigo)}
                      className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                    />
                    <span className="text-slate-700">{p.nombre}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="flex gap-2 border-t border-slate-100 pt-4">
              <Button type="submit">Guardar</Button>
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>
                Cancelar
              </Button>
            </div>
          </form>
        </Card>
      )}

      <Card className="overflow-hidden p-0">
        {loading ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[800px] text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50/80">
                <tr>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Usuario
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Rol
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Placa
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Estado
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody>
                {items.map((u) => (
                  <tr
                    key={u.id_usuario}
                    className="border-b border-slate-100 transition hover:bg-slate-50/60"
                  >
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-900">
                        {u.nombres} {u.apellidos}
                      </p>
                      <p className="text-xs text-slate-500">{u.email}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-700">{u.nombre_rol}</td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-600">{u.numero_placa}</td>
                    <td className="px-4 py-3">
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
                    <td className="px-4 py-3">
                      <div className="flex gap-0.5">
                        <button
                          type="button"
                          className="rounded-lg p-2 text-slate-500 transition hover:bg-brand-50 hover:text-brand-600"
                          onClick={() => openEdit(u)}
                          title="Editar"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          className="rounded-lg p-2 text-slate-500 transition hover:bg-amber-50 hover:text-amber-600"
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
                            <UserX className="h-4 w-4" />
                          ) : (
                            <UserCheck className="h-4 w-4 text-emerald-600" />
                          )}
                        </button>
                        {u.id_usuario !== 1 && (
                          <button
                            type="button"
                            className="rounded-lg p-2 text-slate-500 transition hover:bg-red-50 hover:text-red-600"
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
                            <Trash2 className="h-4 w-4" />
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
