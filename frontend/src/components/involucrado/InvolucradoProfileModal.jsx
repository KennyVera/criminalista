import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  X,
  UserRound,
  Camera,
  Pencil,
  Save,
  ShieldAlert,
  FileText,
  Phone,
  MapPin,
  Calendar,
  IdCard,
  Briefcase,
  Globe,
  Heart,
  ExternalLink,
} from 'lucide-react'
import { involucradosApi } from '../../api/involucrados'
import { Button, Card, Badge, Spinner } from '../ui'
import { useToast } from '../../context/ToastContext'

const TIPO_TONE = {
  Víctima: 'red',
  Testigo: 'blue',
  Sospechoso: 'gray',
}

const GENEROS = ['', 'Masculino', 'Femenino', 'Otro', 'No especificado']

const ESTADO_TONE = {
  Abierto: 'green',
  'En investigación': 'blue',
  Reabierto: 'warning',
  Activo: 'green',
  Cerrado: 'gray',
  Archivado: 'gray',
}

function initials(nombres, apellidos) {
  const a = String(nombres || '').trim().charAt(0)
  const b = String(apellidos || '').trim().charAt(0)
  return (a + b).toUpperCase() || '?'
}

function InfoRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-start gap-2.5">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-indigo-500" />
      <div className="min-w-0">
        <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">{label}</p>
        <p className="break-words text-sm font-medium text-slate-800">
          {value || <span className="text-slate-400">No registrado</span>}
        </p>
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      {children}
    </label>
  )
}

export default function InvolucradoProfileModal({ idInvolucrado, onClose, canEdit = false }) {
  const toast = useToast()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({})
  const [saving, setSaving] = useState(false)
  const [fotoUrl, setFotoUrl] = useState(null)
  const [uploadingFoto, setUploadingFoto] = useState(false)
  const fileRef = useRef(null)
  const objUrlRef = useRef(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await involucradosApi.perfil(idInvolucrado)
      setData(res)
      setForm(res.involucrado || {})
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setLoading(false)
    }
  }, [idInvolucrado, toast])

  const loadFoto = useCallback(async () => {
    try {
      const { blob } = await involucradosApi.fotoBlob(idInvolucrado)
      if (objUrlRef.current) URL.revokeObjectURL(objUrlRef.current)
      const url = URL.createObjectURL(blob)
      objUrlRef.current = url
      setFotoUrl(url)
    } catch {
      setFotoUrl(null)
    }
  }, [idInvolucrado])

  useEffect(() => {
    load()
    loadFoto()
    return () => {
      if (objUrlRef.current) URL.revokeObjectURL(objUrlRef.current)
    }
  }, [load, loadFoto])

  const persona = data?.involucrado || {}
  const stats = data?.estadisticas || {}
  const historial = data?.historial || []

  const onPickFoto = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadingFoto(true)
    const fd = new FormData()
    fd.append('foto', file)
    try {
      await involucradosApi.subirFoto(idInvolucrado, fd)
      toast.success('Foto actualizada', 'La foto de perfil se guardó correctamente')
      await loadFoto()
    } catch (err) {
      toast.error('No se pudo subir la foto', err.message)
    } finally {
      setUploadingFoto(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const save = async () => {
    setSaving(true)
    try {
      const payload = {
        nombres: form.nombres,
        apellidos: form.apellidos,
        identificacion: form.identificacion,
        fecha_nacimiento: form.fecha_nacimiento,
        alias: form.alias,
        genero: form.genero,
        nacionalidad: form.nacionalidad,
        telefono: form.telefono,
        direccion: form.direccion,
        estado_civil: form.estado_civil,
        ocupacion: form.ocupacion,
        antecedentes: form.antecedentes,
        observaciones: form.observaciones,
      }
      await involucradosApi.actualizar(idInvolucrado, payload)
      toast.success('Perfil actualizado', 'Los datos del involucrado se guardaron')
      setEditing(false)
      load()
    } catch (err) {
      toast.error('No se pudo guardar', err.message)
    } finally {
      setSaving(false)
    }
  }

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
      <Card className="glass-card flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden p-0">
        <div className="flex items-center justify-between border-b border-slate-200/70 px-5 py-4">
          <h3 className="flex items-center gap-2 font-semibold text-slate-900">
            <UserRound className="h-5 w-5 text-indigo-600" />
            Perfil del involucrado
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto px-5 py-5">
            {/* Cabecera: foto + identidad */}
            <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start">
              <div className="relative">
                <div className="flex h-28 w-28 items-center justify-center overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-br from-indigo-100 to-violet-100 text-2xl font-bold text-indigo-500 shadow-sm">
                  {fotoUrl ? (
                    <img src={fotoUrl} alt={persona.nombres} className="h-full w-full object-cover" />
                  ) : (
                    initials(persona.nombres, persona.apellidos)
                  )}
                </div>
                {canEdit && (
                  <>
                    <button
                      type="button"
                      onClick={() => fileRef.current?.click()}
                      disabled={uploadingFoto}
                      className="absolute -bottom-2 -right-2 flex h-9 w-9 items-center justify-center rounded-full bg-indigo-600 text-white shadow-lg transition hover:bg-indigo-700 disabled:opacity-50"
                      title="Cambiar foto"
                    >
                      {uploadingFoto ? <Spinner size="sm" /> : <Camera className="h-4 w-4" />}
                    </button>
                    <input
                      ref={fileRef}
                      type="file"
                      accept="image/*"
                      onChange={onPickFoto}
                      className="hidden"
                    />
                  </>
                )}
              </div>

              <div className="flex-1 text-center sm:text-left">
                <h2 className="text-xl font-bold text-slate-900">
                  {persona.nombres} {persona.apellidos}
                </h2>
                {persona.alias && (
                  <p className="text-sm text-slate-500">alias «{persona.alias}»</p>
                )}
                <div className="mt-2 flex flex-wrap justify-center gap-2 sm:justify-start">
                  <Badge tone="gray">ID #{persona.id_involucrado}</Badge>
                  {persona.identificacion && <Badge tone="blue">{persona.identificacion}</Badge>}
                  {persona.edad != null && <Badge tone="gray">{persona.edad} años</Badge>}
                  {stats.total_casos > 0 && (
                    <Badge tone="warning">{stats.total_casos} caso(s)</Badge>
                  )}
                </div>
              </div>

              {canEdit && !editing && (
                <Button size="sm" variant="secondary" onClick={() => setEditing(true)}>
                  <Pencil className="h-3.5 w-3.5" />
                  Editar
                </Button>
              )}
            </div>

            {/* Estadísticas del historial */}
            <div className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {[
                ['Total casos', stats.total_casos || 0, 'text-slate-700'],
                ['Como víctima', stats.como_victima || 0, 'text-rose-600'],
                ['Como sospechoso', stats.como_sospechoso || 0, 'text-amber-600'],
                ['Como testigo', stats.como_testigo || 0, 'text-blue-600'],
              ].map(([label, val, tone]) => (
                <div
                  key={label}
                  className="rounded-xl border border-slate-200/70 bg-white/60 px-3 py-2.5 text-center"
                >
                  <p className={`text-xl font-bold ${tone}`}>{val}</p>
                  <p className="text-[11px] font-medium text-slate-500">{label}</p>
                </div>
              ))}
            </div>

            {/* Datos personales / edición */}
            {editing ? (
              <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
                <Field label="Nombres">
                  <input className="input-field mt-1.5" value={form.nombres || ''} onChange={set('nombres')} />
                </Field>
                <Field label="Apellidos">
                  <input className="input-field mt-1.5" value={form.apellidos || ''} onChange={set('apellidos')} />
                </Field>
                <Field label="Identificación">
                  <input className="input-field mt-1.5" value={form.identificacion || ''} onChange={set('identificacion')} />
                </Field>
                <Field label="Fecha de nacimiento">
                  <input type="date" className="input-field mt-1.5" value={(form.fecha_nacimiento || '').slice(0, 10)} onChange={set('fecha_nacimiento')} />
                </Field>
                <Field label="Alias">
                  <input className="input-field mt-1.5" value={form.alias || ''} onChange={set('alias')} />
                </Field>
                <Field label="Género">
                  <select className="input-field mt-1.5" value={form.genero || ''} onChange={set('genero')}>
                    {GENEROS.map((g) => (
                      <option key={g} value={g}>{g || 'No especificado'}</option>
                    ))}
                  </select>
                </Field>
                <Field label="Nacionalidad">
                  <input className="input-field mt-1.5" value={form.nacionalidad || ''} onChange={set('nacionalidad')} />
                </Field>
                <Field label="Teléfono">
                  <input className="input-field mt-1.5" value={form.telefono || ''} onChange={set('telefono')} />
                </Field>
                <Field label="Estado civil">
                  <input className="input-field mt-1.5" value={form.estado_civil || ''} onChange={set('estado_civil')} />
                </Field>
                <Field label="Ocupación">
                  <input className="input-field mt-1.5" value={form.ocupacion || ''} onChange={set('ocupacion')} />
                </Field>
                <div className="sm:col-span-2">
                  <Field label="Dirección">
                    <input className="input-field mt-1.5" value={form.direccion || ''} onChange={set('direccion')} />
                  </Field>
                </div>
                <div className="sm:col-span-2">
                  <Field label="Antecedentes">
                    <textarea rows={2} className="input-field mt-1.5" value={form.antecedentes || ''} onChange={set('antecedentes')} />
                  </Field>
                </div>
                <div className="sm:col-span-2">
                  <Field label="Observaciones">
                    <textarea rows={2} className="input-field mt-1.5" value={form.observaciones || ''} onChange={set('observaciones')} />
                  </Field>
                </div>
                <div className="flex gap-2 sm:col-span-2">
                  <Button onClick={save} disabled={saving}>
                    {saving ? <Spinner size="sm" /> : <Save className="h-4 w-4" />}
                    Guardar cambios
                  </Button>
                  <Button variant="secondary" onClick={() => { setEditing(false); setForm(persona) }}>
                    Cancelar
                  </Button>
                </div>
              </div>
            ) : (
              <div className="mt-5 grid grid-cols-1 gap-4 rounded-2xl border border-slate-200/70 bg-white/50 p-4 sm:grid-cols-2">
                <InfoRow icon={IdCard} label="Identificación" value={persona.identificacion} />
                <InfoRow icon={Calendar} label="Fecha de nacimiento" value={persona.fecha_nacimiento} />
                <InfoRow icon={Globe} label="Nacionalidad" value={persona.nacionalidad} />
                <InfoRow icon={UserRound} label="Género" value={persona.genero} />
                <InfoRow icon={Phone} label="Teléfono" value={persona.telefono} />
                <InfoRow icon={Heart} label="Estado civil" value={persona.estado_civil} />
                <InfoRow icon={Briefcase} label="Ocupación" value={persona.ocupacion} />
                <InfoRow icon={MapPin} label="Dirección" value={persona.direccion} />
              </div>
            )}

            {/* Antecedentes / observaciones (solo lectura) */}
            {!editing && (persona.antecedentes || persona.observaciones) && (
              <div className="mt-4 space-y-3">
                {persona.antecedentes && (
                  <div className="rounded-xl border border-amber-200/70 bg-amber-50/60 p-3">
                    <p className="flex items-center gap-1.5 text-xs font-semibold text-amber-700">
                      <ShieldAlert className="h-4 w-4" /> Antecedentes
                    </p>
                    <p className="mt-1 text-sm text-slate-700">{persona.antecedentes}</p>
                  </div>
                )}
                {persona.observaciones && (
                  <div className="rounded-xl border border-slate-200/70 bg-slate-50/60 p-3">
                    <p className="text-xs font-semibold text-slate-600">Observaciones</p>
                    <p className="mt-1 text-sm text-slate-700">{persona.observaciones}</p>
                  </div>
                )}
              </div>
            )}

            {/* Historial criminal / expedientes relacionados */}
            <div className="mt-6">
              <h4 className="mb-3 flex items-center gap-2 font-semibold text-slate-900">
                <FileText className="h-4 w-4 text-indigo-600" />
                Historial criminal y expedientes relacionados
              </h4>
              {historial.length === 0 ? (
                <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 px-4 py-6 text-center text-sm text-slate-500">
                  Sin casos vinculados a esta persona.
                </p>
              ) : (
                <ul className="space-y-2">
                  {historial.map((h) => (
                    <li
                      key={h.id_relacion}
                      className="rounded-xl border border-slate-200/70 bg-white/60 px-4 py-3 text-sm shadow-sm"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge tone={TIPO_TONE[h.tipo_relacion] || 'blue'}>{h.tipo_relacion}</Badge>
                        <Link
                          to={`/expedientes/${encodeURIComponent(h.case_number)}`}
                          onClick={onClose}
                          className="inline-flex items-center gap-1 font-semibold text-indigo-600 hover:underline"
                        >
                          {h.case_number}
                          <ExternalLink className="h-3.5 w-3.5" />
                        </Link>
                        <Badge tone={ESTADO_TONE[h.estado] || 'gray'}>{h.estado}</Badge>
                        <span className="ml-auto text-xs text-slate-400">{h.fecha_hecho}</span>
                      </div>
                      <p className="mt-1.5 text-xs text-slate-500">
                        Delito: <span className="font-medium text-slate-700">{h.tipo_delito}</span>
                      </p>
                      {h.declaracion && (
                        <p className="mt-1.5 rounded-lg bg-slate-50/80 px-2.5 py-1.5 text-xs leading-relaxed text-slate-600">
                          {h.declaracion}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}
