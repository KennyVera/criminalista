import { useCallback, useEffect, useState } from 'react'
import { Shield } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Button, Card, Badge } from '../../components/ui'
import { useToast } from '../../context/ToastContext'

const POLICY_META = {
  pwd_min_length: {
    label: 'Longitud mínima contraseña',
    type: 'number',
    min: 6,
    max: 32,
    hint: 'Al crear usuarios o restablecer contraseña.',
  },
  login_max_attempts: {
    label: 'Intentos login máximos',
    type: 'number',
    min: 1,
    max: 50,
    hint: 'Tras superarlos, la cuenta queda bloqueada.',
  },
  session_hours: {
    label: 'Sesión expira (horas)',
    type: 'number',
    min: 1,
    max: 168,
    hint: 'Duración del token JWT y la sesión activa.',
  },
  admin_2fa_required: {
    label: '2FA obligatorio Admin',
    type: 'boolean',
    hint: 'Si está activa y en true, los administradores reciben un código por correo al iniciar sesión.',
  },
}

const INPUT =
  'w-full max-w-xs rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2.5 text-sm text-slate-900 transition focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-100 disabled:cursor-not-allowed disabled:opacity-50'

export default function AdminPoliciesPage() {
  const [items, setItems] = useState([])
  const [draft, setDraft] = useState({})
  const [savingId, setSavingId] = useState(null)
  const toast = useToast()

  const load = useCallback(() => {
    adminApi.politicas().then((d) => {
      const list = d.items || []
      setItems(list)
      const next = {}
      list.forEach((p) => {
        next[p.id_politica] = {
          valor: String(p.valor ?? ''),
          activa: Boolean(p.activa),
        }
      })
      setDraft(next)
    })
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const save = async (row) => {
    const id = row.id_politica
    const state = draft[id]
    if (!state) return
    setSavingId(id)
    try {
      await adminApi.updatePolitica(id, {
        valor: state.valor,
        activa: state.activa,
      })
      toast.success('Éxito', `Política «${row.nombre}» guardada`)
      load()
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setSavingId(null)
    }
  }

  const setValor = (id, valor) => {
    setDraft((prev) => ({
      ...prev,
      [id]: { ...prev[id], valor },
    }))
  }

  const setActiva = (id, activa) => {
    setDraft((prev) => ({
      ...prev,
      [id]: { ...prev[id], activa },
    }))
  }

  const renderValorInput = (row) => {
    const id = row.id_politica
    const meta = POLICY_META[row.clave] || { type: 'text' }
    const value = draft[id]?.valor ?? ''

    if (meta.type === 'boolean') {
      return (
        <select
          value={value === 'true' ? 'true' : 'false'}
          onChange={(e) => setValor(id, e.target.value)}
          className={INPUT}
          disabled={!draft[id]?.activa}
        >
          <option value="false">false — no obligatorio</option>
          <option value="true">true — obligatorio (código por correo)</option>
        </select>
      )
    }

    if (meta.type === 'number') {
      return (
        <input
          type="number"
          min={meta.min}
          max={meta.max}
          value={value}
          onChange={(e) => setValor(id, e.target.value)}
          className={`${INPUT} font-mono`}
          disabled={!draft[id]?.activa}
        />
      )
    }

    return (
      <input
        value={value}
        onChange={(e) => setValor(id, e.target.value)}
        className={INPUT}
        disabled={!draft[id]?.activa}
      />
    )
  }

  return (
    <AdminGuard>
      <AdminPageHeader
        title="Políticas de seguridad"
        subtitle="Configure valores y active o desactive cada regla. Los cambios aplican al guardar."
        icon={Shield}
      />

      <Card className="overflow-hidden p-0">
        {items.length === 0 ? (
          <p className="px-6 py-12 text-center text-sm text-slate-500">
            No hay políticas cargadas. Ejecute el seed de administración.
          </p>
        ) : (
          items.map((p) => {
            const meta = POLICY_META[p.clave]
            const active = draft[p.id_politica]?.activa
            return (
              <div
                key={p.id_politica}
                className={`flex flex-wrap items-start gap-4 border-b border-slate-100 px-5 py-5 transition last:border-0 hover:bg-slate-50/40 ${
                  active ? '' : 'opacity-75'
                }`}
              >
                <div className="min-w-[200px] flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-semibold text-slate-900">{p.nombre}</p>
                    <Badge tone={active ? 'green' : 'slate'}>{active ? 'Activa' : 'Inactiva'}</Badge>
                  </div>
                  <p className="mt-0.5 font-mono text-xs text-slate-400">{p.clave}</p>
                  {(meta?.hint || p.descripcion) && (
                    <p className="mt-1.5 text-xs leading-relaxed text-slate-500">
                      {meta?.hint || p.descripcion}
                    </p>
                  )}
                </div>

                <div className="flex min-w-[140px] flex-col gap-1.5">
                  <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Valor
                  </span>
                  {renderValorInput(p)}
                </div>

                <div className="flex min-w-[120px] flex-col items-start gap-1.5">
                  <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Estado
                  </span>
                  <button
                    type="button"
                    title="Clic para activar o desactivar"
                    onClick={() => setActiva(p.id_politica, !active)}
                    className="transition hover:opacity-80"
                  >
                    <Badge tone={active ? 'green' : 'slate'}>
                      {active ? 'Activa' : 'Inactiva'}
                    </Badge>
                  </button>
                  <span className="text-[10px] text-slate-400">Inactiva = no aplica la regla</span>
                </div>

                <div className="flex items-end self-stretch pb-0.5">
                  <Button
                    type="button"
                    variant="secondary"
                    disabled={savingId === p.id_politica}
                    onClick={() => save(p)}
                  >
                    {savingId === p.id_politica ? 'Guardando…' : 'Guardar'}
                  </Button>
                </div>
              </div>
            )
          })
        )}
      </Card>

      <p className="mt-5 rounded-xl border border-slate-200/80 bg-slate-50/50 px-4 py-3 text-xs leading-relaxed text-slate-500">
        Las políticas activas se aplican de inmediato en nuevos inicios de sesión y al crear o
        cambiar contraseñas. La sesión en curso puede mantener la expiración anterior hasta volver
        a iniciar sesión.
      </p>
    </AdminGuard>
  )
}
