import { useState } from 'react'

const TABS = [
  { id: 'general', label: 'Detalles generales' },
  { id: 'involucrados', label: 'Involucrados' },
  { id: 'evidencias', label: 'Evidencias digitales' },
  { id: 'bitacora', label: 'Bitácora y progreso' },
]

export default function ExpedienteTabs({ active, onChange, children }) {
  return (
    <div className="space-y-6">
      <div
        className="flex flex-wrap gap-1 rounded-xl border border-slate-200 bg-slate-50/80 p-1"
        role="tablist"
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={active === tab.id}
            onClick={() => onChange(tab.id)}
            className={`rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
              active === tab.id
                ? 'bg-white text-brand-700 shadow-sm ring-1 ring-slate-200'
                : 'text-slate-600 hover:bg-white/60 hover:text-slate-900'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div role="tabpanel">{children}</div>
    </div>
  )
}

export { TABS }
