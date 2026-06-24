import { useCallback, useEffect, useRef, useState } from 'react'
import { UserPlus, Users, Camera, ChevronRight } from 'lucide-react'
import { expedientesApi } from '../../../api/expedientes'
import { Button, Card, Badge, Spinner } from '../../../components/ui'
import { useToast } from '../../../context/ToastContext'
import { useAuth } from '../../../context/AuthContext'
import { isAdmin, isComisario, isDetective, isOficial } from '../../../utils/roles'
import InvolucradoProfileModal from '../../../components/involucrado/InvolucradoProfileModal'

const TIPOS = ['Víctima', 'Testigo', 'Sospechoso']
const GENEROS = ['', 'Masculino', 'Femenino', 'Otro', 'No especificado']

const TIPO_TONE = {
  Víctima: 'red',
  Testigo: 'blue',
  Sospechoso: 'gray',
}

const EMPTY_FORM = {
  tipo_relacion: 'Testigo',
  nombres: '',
  apellidos: '',
  identificacion: '',
  fecha_nacimiento: '',
  alias: '',
  genero: '',
  nacionalidad: '',
  telefono: '',
  declaracion: '',
}

export default function TabInvolucrados({ caseNumber }) {
  const toast = useToast()
  const { user } = useAuth()
  const canEdit = isAdmin(user) || isComisario(user) || isDetective(user) || isOficial(user)
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(EMPTY_FORM)
  const [foto, setFoto] = useState(null)
  const [saving, setSaving] = useState(false)
  const [selectedId, setSelectedId] = useState(null)
  const fileRef = useRef(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await expedientesApi.involucrados(caseNumber)
      setItems(res.items || [])
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setLoading(false)
    }
  }, [caseNumber, toast])

  useEffect(() => {
    load()
  }, [load])

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const fd = new FormData()
      Object.entries(form).forEach(([k, v]) => fd.append(k, v ?? ''))
      if (foto) fd.append('foto', foto)
      await expedientesApi.addInvolucradoMultipart(caseNumber, fd)
      toast.success('Guardado', 'Involucrado agregado al expediente')
      setForm(EMPTY_FORM)
      setFoto(null)
      if (fileRef.current) fileRef.current.value = ''
      load()
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setSaving(false)
    }
  }

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="glass-card p-5">
        <div className="mb-4 flex items-center gap-2">
          <Users className="h-5 w-5 text-indigo-600" />
          <h3 className="font-semibold text-slate-900">Personas vinculadas</h3>
        </div>
        {loading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : items.length === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 px-4 py-8 text-center text-sm text-slate-500">
            No hay personas registradas en este expediente.
          </p>
        ) : (
          <ul className="space-y-2.5">
            {items.map((p) => (
              <li key={p.id_relacion}>
                <button
                  type="button"
                  onClick={() => setSelectedId(p.id_involucrado)}
                  className="w-full rounded-xl border border-slate-200/70 bg-white/60 px-4 py-3 text-left text-sm shadow-sm transition hover:border-indigo-300 hover:shadow-md"
                >
                  <div className="flex items-center gap-2">
                    <Badge tone={TIPO_TONE[p.tipo_relacion] || 'blue'}>{p.tipo_relacion}</Badge>
                    <span className="font-semibold text-slate-900">
                      {p.nombres} {p.apellidos}
                    </span>
                    <ChevronRight className="ml-auto h-4 w-4 text-slate-400" />
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Identificación: {p.identificacion || 'No registrada'}
                  </p>
                  {p.declaracion && (
                    <p className="mt-2 rounded-lg bg-slate-50/80 px-2.5 py-1.5 text-xs leading-relaxed text-slate-600">
                      {p.declaracion}
                    </p>
                  )}
                  <p className="mt-2 text-[11px] font-medium text-indigo-500">
                    Ver perfil completo →
                  </p>
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card className="glass-card p-5">
        <h3 className="mb-4 flex items-center gap-2 font-semibold text-slate-900">
          <UserPlus className="h-5 w-5 text-indigo-600" />
          Agregar involucrado
        </h3>
        <form onSubmit={submit} className="space-y-3">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-2xl border border-dashed border-slate-300 bg-slate-50 text-slate-400 transition hover:border-indigo-300 hover:text-indigo-500"
              title="Agregar foto de perfil"
            >
              {foto ? (
                <img
                  src={URL.createObjectURL(foto)}
                  alt="preview"
                  className="h-full w-full object-cover"
                />
              ) : (
                <Camera className="h-5 w-5" />
              )}
            </button>
            <div className="text-xs text-slate-500">
              <p className="font-medium text-slate-700">Foto de perfil (opcional)</p>
              <p>{foto ? foto.name : 'JPG o PNG, hasta unos pocos MB.'}</p>
            </div>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              onChange={(e) => setFoto(e.target.files?.[0] || null)}
              className="hidden"
            />
          </div>

          <label className="block text-sm font-medium text-slate-700">
            Tipo de relación
            <select value={form.tipo_relacion} onChange={set('tipo_relacion')} className="input-field mt-1.5">
              {TIPOS.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block text-sm font-medium text-slate-700">
              Nombres
              <input required value={form.nombres} onChange={set('nombres')} className="input-field mt-1.5" />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Apellidos
              <input required value={form.apellidos} onChange={set('apellidos')} className="input-field mt-1.5" />
            </label>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <label className="block text-sm font-medium text-slate-700">
              Identificación
              <input
                value={form.identificacion}
                onChange={set('identificacion')}
                placeholder="Cédula, pasaporte…"
                className="input-field mt-1.5"
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Fecha de nacimiento
              <input type="date" value={form.fecha_nacimiento} onChange={set('fecha_nacimiento')} className="input-field mt-1.5" />
            </label>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <label className="block text-sm font-medium text-slate-700">
              Alias
              <input value={form.alias} onChange={set('alias')} className="input-field mt-1.5" />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Género
              <select value={form.genero} onChange={set('genero')} className="input-field mt-1.5">
                {GENEROS.map((g) => (
                  <option key={g} value={g}>{g || 'No especificado'}</option>
                ))}
              </select>
            </label>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <label className="block text-sm font-medium text-slate-700">
              Nacionalidad
              <input value={form.nacionalidad} onChange={set('nacionalidad')} className="input-field mt-1.5" />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Teléfono
              <input value={form.telefono} onChange={set('telefono')} className="input-field mt-1.5" />
            </label>
          </div>
          <label className="block text-sm font-medium text-slate-700">
            Declaración / notas
            <textarea
              value={form.declaracion}
              onChange={set('declaracion')}
              rows={2}
              placeholder="Resumen de la declaración o notas relevantes…"
              className="input-field mt-1.5"
            />
          </label>
          <Button type="submit" disabled={saving}>
            {saving ? <Spinner size="sm" /> : <UserPlus className="h-4 w-4" />}
            Agregar involucrado
          </Button>
        </form>
      </Card>

      {selectedId != null && (
        <InvolucradoProfileModal
          idInvolucrado={selectedId}
          canEdit={canEdit}
          onClose={() => {
            setSelectedId(null)
            load()
          }}
        />
      )}
    </div>
  )
}
