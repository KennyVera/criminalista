import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { cn } from '../lib/cn'

export function PasswordInput({ className = '', inputClassName = '', ...props }) {
  const [visible, setVisible] = useState(false)
  return (
    <div className={cn('relative', className)}>
      <input
        {...props}
        type={visible ? 'text' : 'password'}
        className={cn('input-field pr-12', inputClassName)}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        className="absolute right-3 top-1/2 -translate-y-1/2 rounded-xl p-1.5 text-[#94A3B8] transition hover:bg-slate-100 hover:text-[#64748B]"
        aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
      >
        {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  )
}

export function Card({ children, className = '', static: isStatic = false, flush = false }) {
  return (
    <div
      className={cn(
        isStatic ? 'ct-card-static' : 'ct-card',
        flush && 'ct-card-flush',
        !flush && 'p-6',
        className
      )}
    >
      {children}
    </div>
  )
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  type = 'button',
  ...props
}) {
  const variants = {
    primary:
      'bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30 active:scale-[0.98]',
    secondary:
      'border border-slate-200/80 bg-white/90 font-bold text-black shadow-sm backdrop-blur-sm hover:bg-white hover:shadow-md',
    danger: 'bg-[#EF4444] text-white shadow-lg shadow-red-500/20 hover:bg-red-600 active:scale-[0.98]',
    ghost: 'text-[#64748B] hover:bg-white/80 hover:text-[#0F172A]',
    outline:
      'border border-indigo-200/80 bg-white/60 text-[#6366F1] backdrop-blur-sm hover:bg-indigo-50/80',
  }
  const sizes = {
    sm: 'px-4 py-2 text-xs rounded-xl',
    md: 'px-5 py-2.5 text-sm rounded-2xl',
    lg: 'px-6 py-3.5 text-base rounded-2xl',
  }
  return (
    <button
      type={type}
      className={cn(
        'inline-flex items-center justify-center gap-2 font-semibold transition-all duration-200',
        'disabled:cursor-not-allowed disabled:opacity-50',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}

export function Badge({ children, tone = 'info', className = '' }) {
  const tones = {
    info: 'status-badge--info',
    blue: 'status-badge--info',
    green: 'status-badge--active',
    active: 'status-badge--active',
    warning: 'status-badge--warning',
    danger: 'status-badge--danger',
    red: 'status-badge--danger',
    gray: 'status-badge--neutral',
    slate: 'status-badge--neutral',
    neutral: 'status-badge--neutral',
  }
  return <span className={cn('status-badge', tones[tone], className)}>{children}</span>
}

export function Spinner({ size = 'md', className = '' }) {
  const sizes = { sm: 'h-5 w-5', md: 'h-8 w-8', lg: 'h-10 w-10' }
  return (
    <div
      className={cn(
        'animate-spin rounded-full border-2 border-[#6366F1] border-t-transparent',
        sizes[size],
        className
      )}
      role="status"
      aria-label="Cargando"
    />
  )
}

export function EmptyState({ title, description, icon: Icon, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      {Icon && (
        <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-[20px] bg-gradient-to-br from-indigo-50 to-violet-50">
          <Icon className="h-8 w-8 text-[#6366F1]" />
        </div>
      )}
      <p className="text-lg font-bold text-black">{title}</p>
      {description && <p className="mt-2 max-w-sm text-sm font-normal text-black">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}

export function Input({ className = '', ...props }) {
  return <input className={cn('input-field', className)} {...props} />
}

export function Select({ className = '', children, ...props }) {
  return (
    <select className={cn('input-field cursor-pointer', className)} {...props}>
      {children}
    </select>
  )
}

export function Label({ children, className = '', ...props }) {
  return (
    <span className={cn('mb-2 block text-sm font-bold text-black', className)} {...props}>
      {children}
    </span>
  )
}
