import { cn } from '../../lib/cn'

export default function PageHeader({
  title,
  subtitle,
  icon: Icon,
  actions,
  className,
  badge,
  dataset,
}) {
  return (
    <header
      className={cn(
        'mb-2 flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between',
        className
      )}
    >
      <div className="flex min-w-0 items-start gap-5">
        {Icon && (
          <div className="page-icon">
            <Icon className="h-7 w-7" strokeWidth={1.75} />
          </div>
        )}
        <div className="min-w-0 pt-1">
          <h1 className="page-title">{title}</h1>
          {(subtitle || dataset) && (
            <p className="page-subtitle flex flex-wrap items-center gap-2">
              {subtitle}
              {dataset && <code className="code-badge">{dataset}</code>}
            </p>
          )}
          {badge && <div className="mt-3">{badge}</div>}
        </div>
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-3">{actions}</div>}
    </header>
  )
}
