import { FileText, Users, Fingerprint, ClipboardList } from 'lucide-react'

const TABS = [
  { id: 'general', label: 'Detalles generales', icon: FileText },
  { id: 'involucrados', label: 'Involucrados', icon: Users },
  { id: 'evidencias', label: 'Evidencias digitales', icon: Fingerprint },
  { id: 'bitacora', label: 'Bitácora y progreso', icon: ClipboardList },
]

export default function ExpedienteTabs({ active, onChange, children }) {
  return (
    <div className="space-y-6">
      <div
        className="flex flex-wrap gap-1 rounded-xl border border-slate-200/70 bg-slate-100/60 p-1.5 shadow-inner"
        role="tablist"
      >
        {TABS.map((tab) => {
          const Icon = tab.icon
          const isActive = active === tab.id
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => onChange(tab.id)}
              className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
                isActive
                  ? 'bg-white text-indigo-700 shadow-md shadow-indigo-500/10 ring-1 ring-indigo-200/60'
                  : 'text-slate-600 hover:bg-white/70 hover:text-slate-900'
              }`}
            >
              <Icon className={`h-4 w-4 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
              {tab.label}
            </button>
          )
        })}
      </div>
      <div role="tabpanel">{children}</div>
    </div>
  )
}

export { TABS }
