import { useCallback, useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { FileText, Mail, CalendarClock, Trash2, Send, Plus, Power } from 'lucide-react'
import { reporteriaApi } from '../api/reporteria'
import { Button, Card, Input, Select, Spinner } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { canViewOperationalIndicators } from '../utils/roles'

const FREQ_LABEL = { diaria: 'Diaria', semanal: 'Semanal', mensual: 'Mensual' }

export default function ReportesPage() {
  const { user } = useAuth()
  const toast = useToast()
  const allowed = canViewOperationalIndicators(user)

  const [opciones, setOpciones] = useState({ tipos_reporte: [], frecuencias: [] })
  const [schedules, setSchedules] = useState([])
  const [loading, setLoading] = useState(true)

  const [sendForm, setSendForm] = useState({
    tipo_reporte: 'operativo',
    destinatarios: '',
    case_number: '',
    mensaje: '',
  })
  const [sending, setSending] = useState(false)

  const [schedForm, setSchedForm] = useState({
    nombre: '',
    tipo_reporte: 'operativo',
    destinatarios: '',
    frecuencia: 'diaria',
    hora_programada: '08:00',
  })
  const [creating, setCreating] = useState(false)

  const loadSchedules = useCallback(async () => {
    try {
      const res = await reporteriaApi.programados()
      setSchedules(res.items || [])
    } catch (err) {
      toast.error('Reportes', err.message)
    }
  }, [toast])

  useEffect(() => {
    if (!allowed) return
    let active = true
    ;(async () => {
      try {
        const op = await reporteriaApi.opciones()
        if (active) setOpciones(op)
      } catch {
        /* opciones no críticas */
      }
      await loadSchedules()
      if (active) setLoading(false)
    })()
    return () => {
      active = false
    }
  }, [allowed, loadSchedules])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!sendForm.destinatarios.trim()) {
      toast.error('Destinatario requerido', 'Escriba al menos un correo electrónico')
      return
    }
    if (sendForm.tipo_reporte === 'expediente' && !sendForm.case_number.trim()) {
      toast.error('Caso requerido', 'Indique el número de caso del informe')
      return
    }
    setSending(true)
    try {
      const res = await reporteriaApi.enviar(sendForm)
      toast.success('Reporte enviado', `Enviado a ${res.destinatarios.join(', ')}`)
      setSendForm((f) => ({ ...f, mensaje: '' }))
    } catch (err) {
      toast.error('No se pudo enviar', err.message)
    } finally {
      setSending(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!schedForm.destinatarios.trim()) {
      toast.error('Destinatario requerido', 'Escriba al menos un correo electrónico')
      return
    }
    setCreating(true)
    try {
      await reporteriaApi.crearProgramado(schedForm)
      toast.success('Programación creada', 'El reporte se enviará automáticamente')
      setSchedForm((f) => ({ ...f, nombre: '', destinatarios: '' }))
      loadSchedules()
    } catch (err) {
      toast.error('No se pudo programar', err.message)
    } finally {
      setCreating(false)
    }
  }

  const toggleActive = async (s) => {
    try {
      await reporteriaApi.actualizarProgramado(s.id, { activo: !s.activo })
      loadSchedules()
    } catch (err) {
      toast.error('Error', err.message)
    }
  }

  const remove = async (s) => {
    if (!window.confirm(`¿Eliminar la programación «${s.nombre}»?`)) return
    try {
      await reporteriaApi.eliminarProgramado(s.id)
      toast.success('Eliminado', 'Programación eliminada')
      loadSchedules()
    } catch (err) {
      toast.error('Error', err.message)
    }
  }

  if (!allowed) return <Navigate to="/" replace />

  return (
    <section className="mx-auto max-w-7xl space-y-8">
      <header className="page-header">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-gradient-to-br from-indigo-600 to-blue-700 p-3 text-white shadow-lg shadow-indigo-500/25">
            <FileText className="h-6 w-6" />
          </div>
          <div>
            <h2>Reportes</h2>
            <p>
              Genere y envíe reportes por correo electrónico, o programe envíos recurrentes
              automáticos a los destinatarios que defina.
            </p>
          </div>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="glass-card p-5">
          <div className="mb-5 flex items-center gap-2">
            <Mail className="h-5 w-5 text-indigo-600" />
            <h3 className="font-semibold text-slate-900">Enviar reporte por correo</h3>
          </div>
          <form onSubmit={handleSend} className="space-y-4">
            <label className="block text-sm font-medium text-slate-700">
              Tipo de reporte
              <Select
                value={sendForm.tipo_reporte}
                onChange={(e) => setSendForm((f) => ({ ...f, tipo_reporte: e.target.value }))}
                className="mt-1.5"
              >
                {opciones.tipos_reporte.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </Select>
            </label>

            {sendForm.tipo_reporte === 'expediente' && (
              <label className="block text-sm font-medium text-slate-700">
                Número de caso
                <Input
                  value={sendForm.case_number}
                  onChange={(e) => setSendForm((f) => ({ ...f, case_number: e.target.value }))}
                  className="mt-1.5"
                  placeholder="Ej. HZ123456"
                />
              </label>
            )}

            <label className="block text-sm font-medium text-slate-700">
              Destinatario(s)
              <Input
                value={sendForm.destinatarios}
                onChange={(e) => setSendForm((f) => ({ ...f, destinatarios: e.target.value }))}
                className="mt-1.5"
                placeholder="correo@ejemplo.com, otro@ejemplo.com"
              />
              <span className="mt-1 block text-xs text-slate-400">
                Separe varios correos con comas.
              </span>
            </label>

            <label className="block text-sm font-medium text-slate-700">
              Mensaje (opcional)
              <textarea
                value={sendForm.mensaje}
                onChange={(e) => setSendForm((f) => ({ ...f, mensaje: e.target.value }))}
                rows={3}
                className="input-field mt-1.5"
                placeholder="Nota para el destinatario…"
              />
            </label>

            <Button type="submit" disabled={sending}>
              <Send className="h-4 w-4" />
              {sending ? 'Enviando…' : 'Enviar ahora'}
            </Button>
          </form>
        </Card>

        <Card className="glass-card p-5">
          <div className="mb-5 flex items-center gap-2">
            <CalendarClock className="h-5 w-5 text-indigo-600" />
            <h3 className="font-semibold text-slate-900">Programar envío recurrente</h3>
          </div>
          <form onSubmit={handleCreate} className="space-y-4">
            <label className="block text-sm font-medium text-slate-700">
              Nombre de la programación
              <Input
                value={schedForm.nombre}
                onChange={(e) => setSchedForm((f) => ({ ...f, nombre: e.target.value }))}
                className="mt-1.5"
                placeholder="Ej. Resumen operativo semanal"
              />
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block text-sm font-medium text-slate-700">
                Tipo
                <Select
                  value={schedForm.tipo_reporte}
                  onChange={(e) => setSchedForm((f) => ({ ...f, tipo_reporte: e.target.value }))}
                  className="mt-1.5"
                >
                  {opciones.tipos_reporte
                    .filter((t) => t.value === 'operativo')
                    .map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                </Select>
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Frecuencia
                <Select
                  value={schedForm.frecuencia}
                  onChange={(e) => setSchedForm((f) => ({ ...f, frecuencia: e.target.value }))}
                  className="mt-1.5"
                >
                  {(opciones.frecuencias.length ? opciones.frecuencias : ['diaria', 'semanal', 'mensual']).map((fq) => (
                    <option key={fq} value={fq}>
                      {FREQ_LABEL[fq] || fq}
                    </option>
                  ))}
                </Select>
              </label>
            </div>
            <label className="block text-sm font-medium text-slate-700">
              Hora de envío
              <Input
                type="time"
                value={schedForm.hora_programada}
                onChange={(e) => setSchedForm((f) => ({ ...f, hora_programada: e.target.value }))}
                className="mt-1.5"
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Destinatario(s)
              <Input
                value={schedForm.destinatarios}
                onChange={(e) => setSchedForm((f) => ({ ...f, destinatarios: e.target.value }))}
                className="mt-1.5"
                placeholder="correo@ejemplo.com, otro@ejemplo.com"
              />
            </label>
            <Button type="submit" disabled={creating}>
              <Plus className="h-4 w-4" />
              {creating ? 'Creando…' : 'Programar reporte'}
            </Button>
          </form>
        </Card>
      </div>

      <Card className="glass-card p-5">
        <div className="mb-4 flex items-center gap-2">
          <CalendarClock className="h-5 w-5 text-indigo-600" />
          <h3 className="font-semibold text-slate-900">Reportes programados</h3>
        </div>
        {loading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : schedules.length === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 px-4 py-8 text-center text-sm text-slate-500">
            Aún no hay reportes programados.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-3 py-2">Nombre</th>
                  <th className="px-3 py-2">Frecuencia</th>
                  <th className="px-3 py-2">Hora</th>
                  <th className="px-3 py-2">Destinatarios</th>
                  <th className="px-3 py-2">Estado</th>
                  <th className="px-3 py-2">Última ejecución</th>
                  <th className="px-3 py-2 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {schedules.map((s) => (
                  <tr key={s.id} className="border-b border-slate-100 text-slate-700">
                    <td className="px-3 py-2.5 font-medium text-slate-900">{s.nombre}</td>
                    <td className="px-3 py-2.5">{FREQ_LABEL[s.frecuencia] || s.frecuencia}</td>
                    <td className="px-3 py-2.5">{s.hora_programada}</td>
                    <td className="px-3 py-2.5 max-w-[16rem] truncate" title={s.destinatarios}>
                      {s.destinatarios}
                    </td>
                    <td className="px-3 py-2.5">
                      <span
                        className={`status-badge ${
                          s.activo ? 'status-badge--active' : 'status-badge--neutral'
                        }`}
                      >
                        {s.activo ? 'Activo' : 'Pausado'}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-500">
                      {s.ultima_ejecucion ? s.ultima_ejecucion.slice(0, 16).replace('T', ' ') : '—'}
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          type="button"
                          onClick={() => toggleActive(s)}
                          title={s.activo ? 'Pausar' : 'Activar'}
                          className="rounded-lg p-1.5 text-slate-500 transition hover:bg-slate-100 hover:text-indigo-600"
                        >
                          <Power className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => remove(s)}
                          title="Eliminar"
                          className="rounded-lg p-1.5 text-slate-500 transition hover:bg-rose-50 hover:text-rose-600"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </section>
  )
}
