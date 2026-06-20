import { useEffect, useRef, useState } from 'react'
import { MoreVertical } from 'lucide-react'
import { cn } from '../../lib/cn'

export default function RowActionsMenu({ items = [] }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const onDoc = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  if (!items.length) return null

  return (
    <div className="relative inline-block text-left" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
        aria-label="Acciones"
        aria-expanded={open}
      >
        <MoreVertical className="h-4 w-4" />
      </button>
      {open && (
        <div
          className="absolute right-0 z-20 mt-1 min-w-[10rem] rounded-xl border border-slate-200/90 bg-white py-1 shadow-[var(--shadow-elevated)] dark:border-slate-700 dark:bg-slate-900"
          role="menu"
        >
          {items.map((item) => (
            <button
              key={item.label}
              type="button"
              role="menuitem"
              disabled={item.disabled}
              onClick={() => {
                setOpen(false)
                item.onClick?.()
              }}
              className={cn(
                'flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition',
                item.danger
                  ? 'text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40'
                  : 'text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800',
                item.disabled && 'cursor-not-allowed opacity-50'
              )}
            >
              {item.icon && <item.icon className="h-4 w-4 shrink-0" />}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
