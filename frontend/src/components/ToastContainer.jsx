import { Check, Info, AlertTriangle, X } from 'lucide-react'

const STYLES = {
  success: {
    border: 'border-emerald-500',
    iconWrap: 'bg-emerald-500 text-white',
    Icon: Check,
    iconShape: 'rounded-full',
  },
  info: {
    border: 'border-blue-500',
    iconWrap: 'bg-blue-500 text-white',
    Icon: Info,
    iconShape: 'rounded-full',
  },
  warning: {
    border: 'border-amber-400',
    iconWrap: 'bg-amber-400 text-white',
    Icon: AlertTriangle,
    iconShape: 'rounded-full',
  },
  error: {
    border: 'border-red-500',
    iconWrap: 'bg-red-500 text-white',
    Icon: X,
    iconShape: 'rounded-md',
  },
}

function ToastItem({ toast, onDismiss }) {
  const cfg = STYLES[toast.type] || STYLES.info
  const Icon = cfg.Icon

  return (
    <div
      role="alert"
      className={`pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-lg border-2 bg-white p-4 shadow-lg ${cfg.border} animate-[toast-in_0.3s_ease-out]`}
    >
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center ${cfg.iconShape} ${cfg.iconWrap}`}
      >
        <Icon className="h-5 w-5" strokeWidth={2.5} aria-hidden />
      </div>
      <div className="min-w-0 flex-1 pr-6">
        <p className="font-serif text-base font-bold text-slate-800">{toast.title}</p>
        {toast.message ? (
          <p className="mt-0.5 text-sm text-slate-500">{toast.message}</p>
        ) : null}
      </div>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        className="absolute right-3 top-3 cursor-pointer rounded p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
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
        <div key={t.id} className="relative">
          <ToastItem toast={t} onDismiss={onDismiss} />
        </div>
      ))}
    </div>
  )
}
