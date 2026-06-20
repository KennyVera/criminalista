import { cn } from '../../lib/cn'

function initialsFrom(name = '') {
  const parts = String(name).trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  if (parts[0]) return parts[0].slice(0, 2).toUpperCase()
  return '??'
}

export default function UserCell({ name, email, className }) {
  return (
    <div className={cn('flex items-center gap-3', className)}>
      <div className="user-avatar">{initialsFrom(name || email || '')}</div>
      <div className="min-w-0">
        <p className="truncate font-bold text-black">{name || '—'}</p>
        {email && <p className="truncate text-xs font-normal text-black">{email}</p>}
      </div>
    </div>
  )
}
