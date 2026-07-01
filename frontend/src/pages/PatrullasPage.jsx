import { useCallback, useEffect, useMemo, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { Shield, Plus, Users, UserPlus, X, MapPin, Clock } from 'lucide-react'
import { patrullasApi } from '../api/patrullas'
import { Badge, Button, Card, Input, Select, Spinner } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { canManagePatrullas } from '../utils/roles'

const ESTADO_TONE = {
  Disponible: 'green',
  Despachada: 'warning',
  'En ruta': 'warning',
  'En sitio': 'info',
  'Fuera de servicio': 'neutral',
}

export default function PatrullasPage() {
  const { user } = useAuth()
  const toast = useToast()
  const allowed = canManagePatrullas(user)

  const [patrullas, setPatrullas] = useState([])
  const [oficiales, setOficiales] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ sector: '', turno: '', fk_turno: '', notas: '' })
  const [turnos, setTurnos] = useState([])
  const [creating, setCreating] = useState(false)
  const [assignTarget, setAssignTarget] = useState(null)
  const [selected, setSelected] = useState([])
  const [assigning, setAssigning] = useState(false)

  const load = useCallback(async () => {
    try {
      const [pats, ofs] = await Promise.all([
        patrullasApi.listar(),
        patrullasApi.oficialesDisponibles(),
      ])
      setPatrullas(pats.items || [])
      setOficiales(ofs.items || [])
    } catch (err) {
      toast.error('Patrullas', err.message)
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    if (!allowed) return
    patrullasApi.catalogos().then((c) => setTurnos(c.turnos || [])).catch(() => {})
    load()
  }, [allowed, load])

  const disponibles = useMemo(
    () => oficiales.filter((o) => o.disponible),
    [oficiales],
  )

  const onTurnoChange = (fk) => {
    const t = turnos.find((x) => String(x.id_turno) === String(fk))
    setForm((f) => ({
      ...f,
      fk_turno: fk,
      turno: t ? `${t.nombre} (${t.hora_inicio}–${t.hora_fin})` : '',
    }))
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!form.sector.trim() || !form.turno.trim()) {
      toast.error('Datos incompletos', 'Indique el sector y el turno.')
      return
    }
    setCreating(true)
    try {
      await patrullasApi.crear({
        sector: form.sector,
        turno: form.turno,
        fk_turno: form.fk_turno ? Number(form.fk_turno) : undefined,
        notas: form.notas,
      })
      toast.success('Patrulla creada', `${form.sector} · ${form.turno}`)
      setForm({ sector: '', turno: '', fk_turno: '', notas: '' })
      load()
    } catch (err) {
      toast.error('No se pudo crear', err.message)
    } finally {
      setCreating(false)
    }
  }

  const openAssign = (p) => {
    setAssignTarget(p)
    setSelected([])
  }

  const toggleSel = (id) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))

  const handleAssign = async () => {
    if (!selected.length) {
      toast.error('Seleccione oficiales', 'Marque al menos un oficial.')
      return
    }
    setAssigning(true)
    try {
      const res = await patrullasApi.asignarOficiales(assignTarget.id_patrulla, {
        oficial_ids: selected,
      })
      toast.success('Oficiales asignados', `${res.total_asignados} asignado(s) a ${res.codigo}`)
      setAssignTarget(null)
      setSelected([])
      load()
    } catch (err) {
      toast.error('No se pudo asignar', err.message)
    } finally {
      setAssigning(false)
    }
  }

  const removeOficial = async (p, of) => {
    if (!window.confirm(`¿Remover a ${of.oficial_nombre} de ${p.codigo}?`)) return
    try {
      await patrullasApi.removerOficial(p.id_patrulla, of.fk_oficial)
      toast.success('Oficial removido', of.oficial_nombre)
      load()
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
            <Shield className="h-6 w-6" />
          </div>
          <div>
            <h2>Patrullas</h2>
            <p>
              Conforme patrullas por sector y turno, y asigne oficiales operativos (CU-O77).
            </p>
          </div>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        <Card className="glass-card h-fit p-5">
          <div className="mb-5 flex items-center gap-2">
            <Plus className="h-5 w-5 text-indigo-600" />
            <h3 className="font-semibold text-slate-900">Nueva patrulla</h3>
          </div>
          <form onSubmit={handleCreate} className="space-y-4">
            <label className="block text-sm font-medium text-slate-700">
              Sector / zona
              <Input
                value={form.sector}
                onChange={(e) => setForm((f) => ({ ...f, sector: e.target.value }))}
                className="mt-1.5"
                placeholder="Ej. Centro Histórico"
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Turno
              <Select
                value={form.fk_turno}
                onChange={(e) => onTurnoChange(e.target.value)}
                className="mt-1.5"
              >
                <option value="">Seleccione…</option>
                {turnos.map((t) => (
                  <option key={t.id_turno} value={t.id_turno}>
                    {t.nombre} ({t.hora_inicio}–{t.hora_fin})
                  </option>
                ))}
              </Select>
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Notas (opcional)
              <textarea
                value={form.notas}
                onChange={(e) => setForm((f) => ({ ...f, notas: e.target.value }))}
                rows={3}
                className="input-field mt-1.5"
                placeholder="Indicaciones de cobertura…"
              />
            </label>
            <Button type="submit" disabled={creating}>
              <Plus className="h-4 w-4" />
              {creating ? 'Creando…' : 'Crear patrulla'}
            </Button>
          </form>
        </Card>

        <div className="space-y-4">
          {loading ? (
            <div className="flex justify-center py-12">
              <Spinner />
            </div>
          ) : patrullas.length === 0 ? (
            <Card className="glass-card p-8 text-center text-sm text-slate-500">
              Aún no hay patrullas conformadas.
            </Card>
          ) : (
            patrullas.map((p) => (
              <Card key={p.id_patrulla} className="glass-card p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-semibold text-indigo-700">
                        {p.codigo}
                      </span>
                      <Badge tone={ESTADO_TONE[p.estado] || 'neutral'}>{p.estado}</Badge>
                    </div>
                    <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-600">
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5 text-slate-400" /> {p.sector}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5 text-slate-400" /> {p.turno}
                      </span>
                    </div>
                  </div>
                  <Button variant="secondary" onClick={() => openAssign(p)}>
                    <UserPlus className="h-4 w-4" />
                    Asignar oficiales
                  </Button>
                </div>

                <div className="mt-4 border-t border-slate-100 pt-3">
                  <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <Users className="h-3.5 w-3.5" /> Oficiales ({p.total_oficiales})
                  </div>
                  {p.oficiales.length === 0 ? (
                    <p className="text-sm text-slate-400">Sin oficiales asignados.</p>
                  ) : (
                    <ul className="flex flex-wrap gap-2">
                      {p.oficiales.map((of) => (
                        <li
                          key={of.fk_oficial}
                          className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white/70 px-2.5 py-1 text-sm text-slate-700"
                        >
                          <span className="font-medium">{of.oficial_nombre}</span>
                          <span className="text-xs text-slate-400">{of.rol_patrulla}</span>
                          <button
                            type="button"
                            onClick={() => removeOficial(p, of)}
                            title="Remover"
                            className="rounded p-0.5 text-slate-400 transition hover:bg-rose-50 hover:text-rose-600"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </Card>
            ))
          )}
        </div>
      </div>

      {assignTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm">
          <Card className="glass-card w-full max-w-lg p-5">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-semibold text-slate-900">
                Asignar oficiales · {assignTarget.codigo}
              </h3>
              <button
                type="button"
                onClick={() => setAssignTarget(null)}
                className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            {disponibles.length === 0 ? (
              <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/60 px-4 py-6 text-center text-sm text-slate-500">
                No hay oficiales disponibles. Todos están asignados o inactivos.
              </p>
            ) : (
              <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
                {disponibles.map((o) => (
                  <label
                    key={o.id_usuario}
                    className="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-200 bg-white/70 px-3 py-2 text-sm transition hover:border-indigo-300"
                  >
                    <input
                      type="checkbox"
                      checked={selected.includes(o.id_usuario)}
                      onChange={() => toggleSel(o.id_usuario)}
                      className="h-4 w-4 rounded border-slate-300 text-indigo-600"
                    />
                    <span className="font-medium text-slate-800">
                      {o.nombres} {o.apellidos}
                    </span>
                    <span className="ml-auto font-mono text-xs text-slate-400">
                      {o.numero_placa}
                    </span>
                  </label>
                ))}
              </div>
            )}
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setAssignTarget(null)}>
                Cancelar
              </Button>
              <Button onClick={handleAssign} disabled={assigning || !selected.length}>
                <UserPlus className="h-4 w-4" />
                {assigning ? 'Asignando…' : `Asignar (${selected.length})`}
              </Button>
            </div>
          </Card>
        </div>
      )}
    </section>
  )
}
