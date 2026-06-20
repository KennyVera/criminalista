import { cn } from '../../lib/cn'

const SPARKLINES = {
  blue: 'M0,20 L8,16 L16,18 L24,12 L32,14 L40,8 L48,10 L56,4',
  green: 'M0,18 L10,14 L20,16 L30,10 L40,12 L50,6 L56,8',
  purple: 'M0,16 L12,12 L24,14 L36,8 L48,10 L56,6',
}

const ICON_BG = {
  blue: 'bg-indigo-50 text-[#6366F1]',
  green: 'bg-emerald-50 text-[#22C55E]',
  purple: 'bg-violet-50 text-[#8B5CF6]',
}

export default function StatCard({
  label,
  value,
  sub,
  sparkline = 'blue',
  icon: Icon,
  className,
}) {
  const path = SPARKLINES[sparkline] || SPARKLINES.blue
  const stroke =
    sparkline === 'green' ? '#22C55E' : sparkline === 'purple' ? '#8B5CF6' : '#6366F1'

  return (
    <div className={cn('stat-card', className)}>
      <div className="relative z-[1] flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          {Icon && (
            <div
              className={cn(
                'mb-4 flex h-10 w-10 items-center justify-center rounded-2xl',
                ICON_BG[sparkline] || ICON_BG.blue
              )}
            >
              <Icon className="h-5 w-5" strokeWidth={2} />
            </div>
          )}
          <p className="stat-card__label">{label}</p>
          <p className="stat-card__value">{value}</p>
          {sub && <p className="stat-card__sub">{sub}</p>}
        </div>
        <svg
          className="mt-2 h-14 w-28 shrink-0 opacity-40"
          viewBox="0 0 56 24"
          preserveAspectRatio="none"
          aria-hidden
        >
          <path
            d={path}
            fill="none"
            stroke={stroke}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </div>
  )
}
