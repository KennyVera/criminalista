export default function AdminPageHeader({ title, subtitle, icon: Icon, children }) {
  return (
    <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h2 className="flex items-center gap-2 text-xl font-bold text-slate-900">
          {Icon && <Icon className="h-6 w-6 text-brand-600" />}
          {title}
        </h2>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {children}
    </header>
  )
}
