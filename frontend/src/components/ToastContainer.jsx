import { Check, Info, AlertTriangle, X } from 'lucide-react'

const STYLES = {
  success: {
    border: 'border-emerald-200/80',
    bg: 'bg-emerald-50/90',
    iconWrap: 'bg-emerald-500 text-white shadow-emerald-500/30',
    Icon: Check,
    title: 'text-emerald-900',
    message: 'text-emerald-700/80',
  },
  info: {
    border: 'border-brand-200/80',
    bg: 'bg-brand-50/90',
    iconWrap: 'bg-brand-600 text-white shadow-brand-600/30',
    Icon: Info,
    title: 'text-brand-900',
    message: 'text-brand-700/80',
  },
  warning: {
    border: 'border-amber-200/80',
    bg: 'bg-amber-50/90',
    iconWrap: 'bg-amber-500 text-white shadow-amber-500/30',
    Icon: AlertTriangle,
    title: 'text-amber-900',
    message: 'text-amber-700/80',
  },
  error: {
    border: 'border-red-200/80',
    bg: 'bg-red-50/90',
    iconWrap: 'bg-red-500 text-white shadow-red-500/30',
    Icon: X,
    title: 'text-red-900',
    message: 'text-red-700/80',
  },
}

function ToastItem({ toast, onDismiss }) {
  const cfg = STYLES[toast.type] || STYLES.info
  const Icon = cfg.Icon

  return (
    <div
      role="alert"
      className={`pointer-events-auto relative flex w-full max-w-sm items-start gap-3 rounded-2xl border ${cfg.border} ${cfg.bg} p-4 shadow-xl shadow-slate-900/10 backdrop-blur-md animate-[toast-in_0.3s_ease-out]`}
    >
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl shadow-lg ${cfg.iconWrap}`}
      >
        <Icon className="h-4 w-4" strokeWidth={2.5} aria-hidden />
      </div>
      <div className="min-w-0 flex-1 pr-6">
        <p className={`text-sm font-semibold ${cfg.title}`}>{toast.title}</p>
        {toast.message ? (
          <p className={`mt-0.5 text-sm ${cfg.message}`}>{toast.message}</p>
        ) : null}
      </div>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        className="absolute right-3 top-3 cursor-pointer rounded-lg p-1 text-slate-400 transition hover:bg-white/60 hover:text-slate-600"
        aria-label="Cerrar notificación"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

export default function ToastContainer({ toasts, onDismiss }) {
  if (!toasts.length) return null

  return (
    <div
      className="pointer-events-none fixed bottom-4 right-4 z-[9999] flex w-full max-w-sm flex-col gap-3"
      aria-live="polite"
      aria-relevant="additions"
    >
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>
  )
}
