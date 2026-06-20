import { useEffect, useId, useRef, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '../../lib/cn'

const ITEM_HEIGHT_PX = 36

export default function Combobox({
  label,
  value,
  onChange,
  options = [],
  placeholder = 'Seleccionar…',
  disabled = false,
  visibleCount = 10,
  className,
}) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)
  const listId = useId()

  const selected = options.find((opt) => String(opt.value) === String(value))
  const display = selected?.label ?? ''

  useEffect(() => {
    const handleOutside = (event) => {
      if (!rootRef.current?.contains(event.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleOutside)
    return () => document.removeEventListener('mousedown', handleOutside)
  }, [])

  const safeVisible = Math.min(25, Math.max(3, Number(visibleCount) || 10))
  const listMaxHeight = Math.max(1, Math.min(safeVisible, options.length || 1)) * ITEM_HEIGHT_PX

  return (
    <div className={cn('block', open && 'relative z-20', className)} ref={rootRef}>
      {label ? <span className="mb-1.5 block text-xs font-bold text-black">{label}</span> : null}
      <div className="relative">
        <button
          type="button"
          disabled={disabled}
          onClick={() => !disabled && setOpen((prev) => !prev)}
          className={cn(
            'input-field flex w-full cursor-pointer items-center justify-between gap-2 text-left font-normal',
            disabled && 'cursor-not-allowed opacity-60'
          )}
          aria-expanded={open}
          aria-haspopup="listbox"
          aria-controls={listId}
        >
          <span className={cn('truncate', !display && 'text-[#64748B]')}>{display || placeholder}</span>
          <ChevronDown
            className={cn('h-4 w-4 shrink-0 text-black/50 transition-transform', open && 'rotate-180')}
            aria-hidden
          />
        </button>
        {open && (
          <ul
            id={listId}
            role="listbox"
            className="absolute bottom-full z-50 mb-1 w-full overflow-y-auto rounded-2xl border border-slate-200/80 bg-white py-1 shadow-lg"
            style={{ maxHeight: listMaxHeight }}
          >
            {options.map((opt) => {
              const isSelected = String(opt.value) === String(value)
              return (
                <li
                  key={`${opt.value}-${opt.label}`}
                  role="option"
                  aria-selected={isSelected}
                  className={cn(
                    'cursor-pointer px-4 py-2 text-sm font-normal text-black hover:bg-indigo-50',
                    isSelected && 'bg-indigo-50 font-medium text-[#6366F1]'
                  )}
                  onClick={() => {
                    onChange(String(opt.value))
                    setOpen(false)
                  }}
                >
                  {opt.label}
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
