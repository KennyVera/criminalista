import { useEffect, useRef, useState } from 'react'
import { Bell, AlertTriangle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { adminApi } from '../api/admin'
import { useAuth } from '../context/AuthContext'
import { isAdmin, isComisario } from '../utils/roles'

export default function BackupAlertsBell() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [alerts, setAlerts] = useState([])
  const ref = useRef(null)

  const canSee = isAdmin(user) || isComisario(user)

  useEffect(() => {
    if (!canSee) return undefined
    const load = () =>
      adminApi.respaldosAlertas(72).then((d) => setAlerts(d.items || [])).catch(() => {})
    load()
    const id = setInterval(load, 60_000)
    return () => clearInterval(id)
  }, [canSee])

  useEffect(() => {
    const onDoc = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  if (!canSee) return null

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="relative rounded-2xl p-2.5 text-[#64748B] transition hover:bg-white/80 hover:text-[#0F172A]"
        aria-label="Alertas de respaldo"
      >
        <Bell className="h-5 w-5" />
        {alerts.length > 0 && (
          <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {alerts.length > 9 ? '9+' : alerts.length}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 rounded-[20px] border border-white/90 bg-white/95 p-0 shadow-[var(--shadow-elevated)] backdrop-blur-xl">
          <div className="border-b px-4 py-3">
            <p className="font-semibold text-slate-900">Alertas de respaldo</p>
            <p className="text-xs text-slate-500">Fallos en las últimas 72 h</p>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {alerts.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-slate-500">
                Sin fallos recientes.
              </p>
            ) : (
              alerts.map((a) => (
                <div
                  key={a.id}
                  className="flex gap-2 border-b border-slate-50 px-4 py-3 text-sm last:border-0"
                >
                  <AlertTriangle className="h-4 w-4 shrink-0 text-red-500" />
                  <div>
                    <p className="font-medium text-slate-800">{a.nombre_config}</p>
                    <p className="text-xs text-slate-500">{a.detalle}</p>
                  </div>
                </div>
              ))
            )}
          </div>
          {isAdmin(user) && (
            <div className="border-t px-4 py-2">
              <Link
                to="/admin/respaldos"
                className="text-xs font-medium text-brand-600 hover:underline"
                onClick={() => setOpen(false)}
              >
                Ir a configurar respaldos
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
