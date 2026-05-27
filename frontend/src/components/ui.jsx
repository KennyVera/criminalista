import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'

export function PasswordInput({
  className = '',
  inputClassName = '',
  ...props
}) {
  const [visible, setVisible] = useState(false)
  return (
    <div className={`relative ${className}`}>
      <input
        {...props}
        type={visible ? 'text' : 'password'}
        className={`w-full rounded-xl border border-slate-200 py-2.5 pl-3 pr-11 text-sm focus:border-brand-500 focus:ring-2 focus:ring-brand-100 ${inputClassName}`}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        className="absolute right-2 top-1/2 -translate-y-1/2 cursor-pointer rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
        aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
      >
        {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  )
}

export function Card({ children, className = '' }) {
  return (
    <div
      className={`rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-200/50 ${className}`}
    >
      {children}
    </div>
  )
}

export function Button({
  children,
  variant = 'primary',
  className = '',
  type = 'button',
  ...props
}) {
  const variants = {
    primary:
      'bg-brand-600 text-white hover:bg-brand-700 active:bg-brand-700 shadow-sm shadow-brand-600/25',
    secondary:
      'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50',
    danger: 'bg-red-600 text-white hover:bg-red-700',
    ghost: 'text-slate-600 hover:bg-slate-100',
  }
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

export function Badge({ children, tone = 'blue' }) {
  const tones = {
    blue: 'bg-brand-50 text-brand-700 ring-brand-100',
    green: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
    gray: 'bg-slate-100 text-slate-600 ring-slate-200',
    slate: 'bg-slate-100 text-slate-600 ring-slate-200',
    red: 'bg-red-50 text-red-700 ring-red-100',
  }
  return (
    <span
      className={`inline-flex items-center rounded-lg px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${tones[tone]}`}
    >
      {children}
    </span>
  )
}

export function Spinner() {
  return (
    <div
      className="h-8 w-8 animate-spin rounded-full border-2 border-brand-600 border-t-transparent"
      role="status"
      aria-label="Cargando"
    />
  )
}

export function EmptyState({ title, description }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <p className="text-lg font-medium text-slate-800">{title}</p>
      <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>
    </div>
  )
}

