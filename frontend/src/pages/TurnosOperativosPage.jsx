import { useCallback, useEffect, useMemo, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { CalendarClock, UserPlus, XCircle, RefreshCw } from 'lucide-react'
import { patrullasApi } from '../api/patrullas'
import { Button, Card, Badge, Spinner } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { canManagePatrullas } from '../utils/roles'

export default function TurnosOperativosPage() {
  const { user } = useAuth()
  const toast = useToast()
  const allowed = canManagePatrullas(user)

  const [fecha, setFecha] = useState(() => new Date().toISOString().slice(0, 10))
  const [turnos, setTurnos] = useState([])
  const [asignaciones, setAsignaciones] = useState([])
  const [personal, setPersonal] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ fk_turno: '', fk_usuario: '', notas: '' })
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await patrullasApi.turnos({ fecha })
      setTurnos(res.turnos || [])
      setAsignaciones(res.asignaciones || [])
      setPersonal(res.personal || [])
    } catch (e) {
      toast.error('Turnos', e.message)
    } finally {
      setLoading(false)
    }
  }, [fecha, toast])

  useEffect(() => {
    if (allowed) load()
  }, [allowed, load])

  const porTurno = useMemo(() => {
    const map = {}
    turnos.forEach((t) => {
      map[t.id_turno] = asignaciones.filter((a) => Number(a.fk_turno) === Number(t.id_turno))
    })
    return map
  }, [turnos, asignaciones])

  const asignar = async (e) => {
    e.preventDefault()
    if (!form.fk_turno || !form.fk_usuario) {
      toast.error('Datos incompletos', 'Seleccione turno y personal.')
      return
    }
    setSaving(true)
    try {
      await patrullasApi.asignarTurno({
        fk_turno: Number(form.fk_turno),
        fk_usuario: Number(form.fk_usuario),
        fecha,
        notas: form.notas,
      })
      toast.success('Asignado', 'Personal asignado al turno.')
      setForm({ fk_turno: '', fk_usuario: '', notas: '' })
      load()
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setSaving(false)
    }
  }

  const cerrar = async (id) => {
    if (!window.confirm('¿Cerrar esta asignación de turno?')) return
    try {
      await patrullasApi.cerrarAsignacionTurno(id)
      toast.success('Cerrado', 'Asignación finalizada.')
      load()
    } catch (err) {
      toast.error('Error', err.message)
    }
  }

  if (!allowed) return <Navigate to="/" replace />

  return (
    <section className="mx-auto max-w-6xl space-y-8">
      <header className="page-header">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-gradient-to-br from-violet-600 to-indigo-700 p-3 text-white shadow-lg shadow-violet-500/25">
            <CalendarClock className="h-6 w-6" />
          </div>
          <div>
            <h2>Turnos operativos</h2>
            <p>
              Registro diario de turnos (mañana, tarde, noche, madrugada) y personal en servicio.
              Permite saber quién estaba trabajando cuando ocurrió un incidente.
            </p>
          </div>
        </div>
      </header>

      <div className="flex flex-wrap items-end justify-between gap-3">
        <label className="text-sm font-medium text-slate-700">
          Fecha
          <input
            type="date"
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
            className="input-field ml-2 mt-1 !w-auto"
          />
        </label>
        <Button type="button" variant="secondary" onClick={load} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>

      <Card className="glass-card p-5">
        <div className="mb-4 flex items-center gap-2">
          <UserPlus className="h-5 w-5 text-violet-600" />
          <h3 className="font-semibold text-slate-900">Nueva asignación de turno</h3>
        </div>
        <form onSubmit={asignar} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="block text-sm font-medium text-slate-700">
            Turno
            <select
              value={form.fk_turno}
              onChange={(e) => setForm((f) => ({ ...f, fk_turno: e.target.value }))}
              className="input-field mt-1.5"
              required
            >
              <option value="">Seleccionar…</option>
              {turnos.map((t) => (
                <option key={t.id_turno} value={t.id_turno}>
                  {t.nombre} ({t.hora_inicio}–{t.hora_fin})
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-medium text-slate-700 sm:col-span-2">
            Personal
            <select
              value={form.fk_usuario}
              onChange={(e) => setForm((f) => ({ ...f, fk_usuario: e.target.value }))}
              className="input-field mt-1.5"
              required
            >
              <option value="">Seleccionar…</option>
              {personal.map((p) => (
                <option key={p.id_usuario} value={p.id_usuario}>
                  {p.etiqueta} · {p.nombre_rol}
                </option>
              ))}
            </select>
          </label>
          <div className="flex items-end">
            <Button type="submit" disabled={saving} className="w-full">
              {saving ? 'Guardando…' : 'Asignar'}
            </Button>
          </div>
        </form>
      </Card>

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {turnos.map((t) => (
            <Card key={t.id_turno} className="glass-card p-5">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900">{t.nombre}</h3>
                  <p className="text-xs text-slate-500">
                    {t.hora_inicio} – {t.hora_fin}
                  </p>
                </div>
                <Badge tone="slate">{(porTurno[t.id_turno] || []).length} en servicio</Badge>
              </div>
              <ul className="space-y-2">
                {(porTurno[t.id_turno] || []).length === 0 ? (
                  <li className="text-sm text-slate-500">Sin personal asignado.</li>
                ) : (
                  (porTurno[t.id_turno] || []).map((a) => (
                    <li
                      key={a.id_asignacion_turno}
                      className="flex items-center justify-between gap-2 rounded-xl border border-slate-200/80 px-3 py-2 text-sm"
                    >
                      <div>
                        <p className="font-medium text-slate-900">{a.usuario_nombre}</p>
                        <p className="text-xs text-slate-500">
                          {a.rol_nombre} · {a.usuario_placa}
                        </p>
                      </div>
                      {a.estado === 'Activa' && (
                        <button
                          type="button"
                          onClick={() => cerrar(a.id_asignacion_turno)}
                          className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                          title="Cerrar asignación"
                        >
                          <XCircle className="h-4 w-4" />
                        </button>
                      )}
                    </li>
                  ))
                )}
              </ul>
            </Card>
          ))}
        </div>
      )}
    </section>
  )
}
