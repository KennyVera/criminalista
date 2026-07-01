import { useCallback, useEffect, useMemo, useState } from 'react'
import { UserPlus, Pencil, Trash2, UserCheck, UserX, RefreshCw, Search } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Button, Card, Badge, Spinner, PasswordInput } from '../../components/ui'
import Combobox from '../../components/ui/Combobox'
import UserAvatar, { useAdminUserPhotoUrls, userPhotoVersion } from '../../components/UserAvatar'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../../context/ToastContext'
import { EMAIL_HINT, validateEmailAddress } from '../../utils/emailValidation'

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
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [rolePermsPreview, setRolePermsPreview] = useState([])
  const [generatingPlaca, setGeneratingPlaca] = useState(false)
  const [emailError, setEmailError] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const toast = useToast()
  const { user: currentUser, photoEpoch } = useAuth()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [u, r] = await Promise.all([adminApi.users(), adminApi.roles()])
      setItems(u.items || [])
      setRoles(r.items || [])
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (!currentUser?.id_usuario) return
    setItems((prev) =>
      prev.map((u) =>
        Number(u.id_usuario) === Number(currentUser.id_usuario)
          ? {
              ...u,
              tiene_foto: currentUser.tiene_foto,
              foto_actualizada_en: currentUser.foto_actualizada_en,
              nombres: currentUser.nombres,
              apellidos: currentUser.apellidos,
            }
          : u
      )
    )
  }, [photoEpoch, currentUser])

  useEffect(() => {
    if (!formOpen || !form.fk_rol) {
      setRolePermsPreview([])
      return
    }
    let cancelled = false
    adminApi
      .rolPermisos(Number(form.fk_rol))
      .then((rp) => {
        if (!cancelled) {
          const list = rp.permisos || []
          setRolePermsPreview(list.map((p) => p.nombre || p.codigo))
        }
      })
      .catch(() => {
        if (!cancelled) setRolePermsPreview([])
      })
    return () => {
      cancelled = true
    }
  }, [formOpen, form.fk_rol])

  const openCreate = () => {
    setEditing(null)
    setForm(emptyForm)
    setEmailError('')
    setFormOpen(true)
  }

  const generatePlaca = async (fkRol = form.fk_rol) => {
    setGeneratingPlaca(true)
    try {
      const res = await adminApi.generatePlaca(Number(fkRol))
      setForm((prev) => ({ ...prev, numero_placa: res.numero_placa }))
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setGeneratingPlaca(false)
    }
  }

  const openEdit = (user) => {
    setEditing(user)
    setEmailError('')
    setForm({
      nombres: user.nombres,
      apellidos: user.apellidos,
      email: user.email,
      numero_placa: user.numero_placa,
      fk_rol: user.fk_rol,
      password: '',
      estado_cuenta: user.estado_cuenta,
    })
    setFormOpen(true)
  }

  const validateFormEmail = (value = form.email) => {
    const result = validateEmailAddress(value)
    if (!result.ok) {
      setEmailError(result.message)
      return false
    }
    setEmailError('')
    return true
  }

  const save = async (e) => {
    e.preventDefault()
    if (!validateFormEmail()) {
      return
    }
    if (!editing && !form.numero_placa) {
      toast.error('Error', 'Genera un número de placa antes de guardar')
      return
    }
    try {
      const body = { ...form, fk_rol: Number(form.fk_rol) }
      if (editing) {
        delete body.numero_placa
        if (!body.password) delete body.password
        await adminApi.updateUser(editing.id_usuario, body)
        toast.success('Éxito', 'Usuario actualizado correctamente')
      } else {
        const created = await adminApi.createUser(body)
        if (created.email_sent) {
          toast.success('Éxito', 'Usuario registrado. Se enviaron las credenciales por correo.')
        } else {
          toast.success('Éxito', 'Usuario registrado correctamente')
          if (created.email_error) {
            toast.error(
              'Correo no enviado',
              'El usuario se creó, pero no se pudieron enviar las credenciales por email.'
            )
          }
        }
      }
      setFormOpen(false)
      load()
    } catch (err) {
      toast.error('Error', err.message)
    }
  }

  const selectedRoleName =
    roles.find((r) => Number(r.id_rol) === Number(form.fk_rol))?.nombre_rol || 'Rol'

  const roleFilterOptions = useMemo(
    () => [
      { value: '', label: 'Todos los roles' },
      ...roles.map((r) => ({
        value: String(r.id_rol),
        label: r.nombre_rol,
      })),
    ],
    [roles]
  )

  const filteredItems = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    return items.filter((u) => {
      if (roleFilter && String(u.fk_rol) !== String(roleFilter)) {
        return false
      }
      if (!q) return true
      const haystack = [
        u.nombres,
        u.apellidos,
        `${u.nombres} ${u.apellidos}`,
        u.email,
        u.numero_placa,
        u.nombre_rol,
        u.estado_cuenta,
        String(u.id_usuario),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(q)
    })
  }, [items, roleFilter, searchQuery])

  const hasActiveFilters = Boolean(searchQuery.trim() || roleFilter)

  const photoUrls = useAdminUserPhotoUrls(items, currentUser?.id_usuario, photoEpoch)

  const clearFilters = () => {
    setSearchQuery('')
    setRoleFilter('')
  }

  return (
    <AdminGuard>
      <AdminPageHeader
        title="Registrar y editar usuarios"
        subtitle="Asigna un rol; los permisos se heredan automáticamente del rol (configúralos en Roles y permisos)."
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
              <div>
                <input
                  type="email"
                  placeholder="Email"
                  value={form.email}
                  onChange={(e) => {
                    setForm({ ...form, email: e.target.value })
                    if (emailError) setEmailError('')
                  }}
                  onBlur={(e) => validateFormEmail(e.target.value)}
                  className={`${INPUT} ${emailError ? 'border-red-300 focus:border-red-500 focus:ring-red-100' : ''}`}
                  required
                />
                {emailError ? (
                  <p className="mt-1 text-xs text-red-600">{emailError}</p>
                ) : (
                  <p className="mt-1 text-xs text-slate-500">{EMAIL_HINT}</p>
                )}
              </div>
              <div className="space-y-2">
                <div className="flex gap-2">
                  <input
                    placeholder="Número placa"
                    value={form.numero_placa}
                    readOnly
                    className={`${INPUT} flex-1 cursor-not-allowed bg-slate-100 text-slate-700`}
                    required={!editing}
                  />
                  {!editing && (
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => generatePlaca()}
                      disabled={generatingPlaca}
                      className="h-[42px] shrink-0 whitespace-nowrap"
                    >
                      <RefreshCw className={`h-4 w-4 ${generatingPlaca ? 'animate-spin' : ''}`} />
                      {form.numero_placa ? 'Regenerar' : 'Generar'}
                    </Button>
                  )}
                </div>
                {editing && (
                  <p className="text-xs text-slate-500">La placa no se puede modificar tras el registro.</p>
                )}
              </div>
              <select
                value={form.fk_rol}
                onChange={(e) =>
                  setForm({
                    ...form,
                    fk_rol: e.target.value,
                    numero_placa: editing ? form.numero_placa : '',
                  })
                }
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
            <div className="rounded-xl border border-slate-200 bg-slate-50/60 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Permisos heredados del rol
              </p>
              <p className="mt-1 text-sm text-slate-600">
                El usuario recibirá los permisos definidos para{' '}
                <strong className="text-slate-800">{selectedRoleName}</strong>. Para modificarlos,
                usa la pantalla{' '}
                <a href="/admin/permisos" className="font-medium text-brand-600 hover:underline">
                  Roles y permisos
                </a>
                .
              </p>
              {rolePermsPreview.length > 0 ? (
                <ul className="mt-3 flex flex-wrap gap-2">
                  {rolePermsPreview.map((label) => (
                    <li
                      key={label}
                      className="rounded-full border border-slate-200 bg-white px-2.5 py-0.5 text-xs text-slate-700"
                    >
                      {label}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-xs text-slate-500">Cargando permisos del rol…</p>
              )}
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
          <>
            <div className="flex flex-wrap items-end gap-3 border-b border-slate-100 bg-slate-50/40 px-4 py-4">
              <div className="relative min-w-[220px] flex-1">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  type="search"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Buscar por nombre, email, placa, rol…"
                  className={`${INPUT} pl-10`}
                  aria-label="Buscar usuarios"
                />
              </div>
              <div className="w-full sm:w-56">
                <Combobox
                  label="Rol"
                  value={roleFilter}
                  onChange={setRoleFilter}
                  options={roleFilterOptions}
                  placeholder="Todos los roles"
                />
              </div>
              {hasActiveFilters && (
                <Button type="button" variant="secondary" onClick={clearFilters}>
                  Limpiar filtros
                </Button>
              )}
            </div>
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
                {filteredItems.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-12 text-center text-sm text-slate-500">
                      {hasActiveFilters
                        ? 'No hay usuarios que coincidan con la búsqueda o el rol seleccionado.'
                        : 'No hay usuarios registrados.'}
                    </td>
                  </tr>
                ) : (
                  filteredItems.map((u) => (
                  <tr
                    key={u.id_usuario}
                    className="border-b border-slate-100 transition hover:bg-slate-50/60"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-brand-600 to-indigo-600 shadow-sm">
                          <UserAvatar
                            key={`${u.id_usuario}-${userPhotoVersion(u)}`}
                            user={u}
                            className="h-full w-full"
                            textClassName="text-xs"
                            photoUrl={photoUrls[u.id_usuario] ?? null}
                            managedPhoto
                          />
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-slate-900">
                            {u.nombres} {u.apellidos}
                          </p>
                          <p className="text-xs text-slate-500">{u.email}</p>
                        </div>
                      </div>
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
                  ))
                )}
              </tbody>
            </table>
            </div>
            {filteredItems.length > 0 && hasActiveFilters && (
              <p className="border-t border-slate-100 px-4 py-2 text-xs text-slate-500">
                Mostrando {filteredItems.length} de {items.length} usuario
                {items.length === 1 ? '' : 's'}
              </p>
            )}
          </>
        )}
      </Card>
    </AdminGuard>
  )
}
