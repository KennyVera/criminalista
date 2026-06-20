import { cn } from '../../lib/cn'

export default function InfoPanel({ title, children, icon: Icon, action, className }) {
  return (
    <div className={cn('info-panel', className)}>
      {Icon && (
        <Icon className="info-panel__icon-bg h-20 w-20 text-slate-900 dark:text-slate-100" strokeWidth={1} />
      )}
      <div className="relative">
        <h3 className="info-panel__title">{title}</h3>
        <div className="info-panel__body">{children}</div>
        {action && <div className="mt-3">{action}</div>}
      </div>
    </div>
  )
}
