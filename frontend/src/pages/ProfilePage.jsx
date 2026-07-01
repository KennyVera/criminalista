import { useCallback, useEffect, useRef, useState } from 'react'
import { Camera, Mail, Phone, Shield, UserRound, Trash2 } from 'lucide-react'
import PageHeader from '../components/layout/PageHeader'
import UserAvatar, { userInitials, userPhotoVersion } from '../components/UserAvatar'
import { Button, Card, Spinner } from '../components/ui'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const INPUT =
  'mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2.5 text-sm text-slate-900 transition focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-100'

export default function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const toast = useToast()
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploadingFoto, setUploadingFoto] = useState(false)
  const [previewUrl, setPreviewUrl] = useState(null)
  const fileRef = useRef(null)
  const previewRef = useRef(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.authProfile()
      setProfile(data)
      setForm({
        nombres: data.nombres || '',
        apellidos: data.apellidos || '',
        telefono: data.telefono || '',
        biografia: data.biografia || '',
      })
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    load()
    return () => {
      if (previewRef.current) {
        URL.revokeObjectURL(previewRef.current)
        previewRef.current = null
      }
    }
  }, [load])

  const clearPreview = () => {
    if (previewRef.current) {
      URL.revokeObjectURL(previewRef.current)
      previewRef.current = null
    }
    setPreviewUrl(null)
  }

  const save = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const updated = await api.authUpdateProfile(form)
      setProfile(updated)
      await refreshUser()
      toast.success('Éxito', 'Perfil actualizado correctamente')
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setSaving(false)
    }
  }

  const onPickFoto = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      toast.error('Error', 'Selecciona un archivo de imagen')
      return
    }
    setUploadingFoto(true)
    const localPreview = URL.createObjectURL(file)
    if (previewRef.current) URL.revokeObjectURL(previewRef.current)
    previewRef.current = localPreview
    setPreviewUrl(localPreview)
    try {
      const fd = new FormData()
      fd.append('foto', file)
      const updated = await api.authUploadProfileFoto(fd)
      setProfile(updated)
      clearPreview()
      await refreshUser()
      toast.success('Éxito', 'Foto de perfil actualizada')
    } catch (err) {
      clearPreview()
      toast.error('Error', err.message)
    } finally {
      setUploadingFoto(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const removeFoto = async () => {
    if (!confirm('¿Quitar la foto de perfil?')) return
    setUploadingFoto(true)
    try {
      const updated = await api.authRemoveProfileFoto()
      setProfile(updated)
      clearPreview()
      await refreshUser()
      toast.success('Éxito', 'Foto eliminada')
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setUploadingFoto(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner />
      </div>
    )
  }

  const displayUser = profile || user

  return (
    <section className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        title="Mi perfil"
        subtitle="Actualiza tu información personal y foto de perfil."
        icon={UserRound}
      />

      <Card className="overflow-hidden border-brand-200/40 bg-gradient-to-br from-brand-50/20 to-white">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center">
          <div className="relative mx-auto sm:mx-0">
            <div className="flex h-28 w-28 items-center justify-center overflow-hidden rounded-2xl bg-gradient-to-br from-brand-600 to-indigo-600 shadow-lg shadow-brand-600/25">
              <UserAvatar
                key={`${displayUser?.id_usuario}-${userPhotoVersion(displayUser)}-${previewUrl || 'remote'}`}
                user={displayUser}
                className="h-full w-full"
                textClassName="text-2xl"
                photoUrl={previewUrl}
                managedPhoto={Boolean(previewUrl)}
                photoVersion={userPhotoVersion(displayUser)}
              />
            </div>
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              disabled={uploadingFoto}
              className="absolute -bottom-2 -right-2 flex h-9 w-9 items-center justify-center rounded-xl border border-white bg-white text-slate-700 shadow-md transition hover:bg-brand-50 hover:text-brand-600"
              title="Cambiar foto"
            >
              {uploadingFoto ? <Spinner size="sm" /> : <Camera className="h-4 w-4" />}
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={onPickFoto}
            />
          </div>
          <div className="flex-1 text-center sm:text-left">
            <h2 className="text-xl font-bold text-slate-900">
              {displayUser?.nombres} {displayUser?.apellidos}
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              {displayUser?.nombre_rol}
              {displayUser?.numero_placa ? ` · ${displayUser.numero_placa}` : ''}
            </p>
            <p className="mt-1 text-sm text-slate-500">{displayUser?.email}</p>
            {displayUser?.tiene_foto && (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="mt-3"
                onClick={removeFoto}
                disabled={uploadingFoto}
              >
                <Trash2 className="h-3.5 w-3.5" />
                Quitar foto
              </Button>
            )}
            {!displayUser?.tiene_foto && (
              <p className="mt-2 text-xs text-slate-400">
                Sin foto: se muestran tus iniciales ({userInitials(displayUser)})
              </p>
            )}
          </div>
        </div>
      </Card>

      <Card>
        <form onSubmit={save} className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-sm font-medium text-slate-700">
              Nombres
              <input
                className={INPUT}
                value={form.nombres}
                onChange={(e) => setForm({ ...form, nombres: e.target.value })}
                required
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Apellidos
              <input
                className={INPUT}
                value={form.apellidos}
                onChange={(e) => setForm({ ...form, apellidos: e.target.value })}
                required
              />
            </label>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-sm font-medium text-slate-700">Correo electrónico</p>
              <div className="mt-1.5 flex items-center gap-2 rounded-xl border border-dashed border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-600">
                <Mail className="h-4 w-4 shrink-0 text-slate-400" />
                {displayUser?.email}
              </div>
              <p className="mt-1 text-xs text-slate-400">Solo un administrador puede cambiar el correo.</p>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-700">Número de placa</p>
              <div className="mt-1.5 flex items-center gap-2 rounded-xl border border-dashed border-slate-200 bg-slate-50 px-3 py-2.5 font-mono text-sm text-slate-600">
                <Shield className="h-4 w-4 shrink-0 text-slate-400" />
                {displayUser?.numero_placa || '—'}
              </div>
            </div>
          </div>

          <label className="block text-sm font-medium text-slate-700">
            Teléfono
            <div className="relative mt-1.5">
              <Phone className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                className={`${INPUT} mt-0 pl-10`}
                value={form.telefono}
                onChange={(e) => setForm({ ...form, telefono: e.target.value })}
                placeholder="Opcional"
              />
            </div>
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Biografía breve
            <textarea
              className={`${INPUT} min-h-[96px] resize-y`}
              value={form.biografia}
              onChange={(e) => setForm({ ...form, biografia: e.target.value })}
              maxLength={500}
              placeholder="Información adicional sobre tu rol o contacto..."
            />
            <span className="mt-1 block text-right text-xs text-slate-400">
              {form.biografia.length}/500
            </span>
          </label>

          <div className="flex justify-end border-t border-slate-100 pt-4">
            <Button type="submit" disabled={saving}>
              {saving ? 'Guardando…' : 'Guardar cambios'}
            </Button>
          </div>
        </form>
      </Card>
    </section>
  )
}
