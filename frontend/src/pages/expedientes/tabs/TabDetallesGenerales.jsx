import { useEffect, useState } from 'react'
import { MapPin, Database, AlertTriangle } from 'lucide-react'
import { expedientesApi } from '../../../api/expedientes'
import { Card, Spinner } from '../../../components/ui'

function Field({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-100/80 bg-slate-50/50 px-3 py-2.5">
      <dt className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        {label}
      </dt>
      <dd className="mt-1 text-sm font-medium text-slate-900">{value ?? '—'}</dd>
    </div>
  )
}

export default function TabDetallesGenerales({ caseNumber }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    expedientesApi
      .detallesGenerales(caseNumber)
      .then((res) => {
        if (!cancelled) setData(res)
      })
      .catch((e) => {
        if (!cancelled) setError(e.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [caseNumber])

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner />
      </div>
    )
  }

  if (error) {
    return (
      <Card className="glass-card flex items-start gap-3 p-6 text-sm text-red-700">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
        <p>No se pudo cargar la información del expediente: {error}</p>
      </Card>
    )
  }

  if (!data?.found) {
    return (
      <Card className="glass-card p-6 text-sm text-slate-600">
        {data?.message || 'No hay datos disponibles para este expediente.'}
      </Card>
    )
  }

  const r = data.resumen || {}

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <Database className="h-3.5 w-3.5 text-indigo-500" />
        <span>
          Fuente: <span className="font-medium text-slate-700">{data.source}</span> ·{' '}
          {r.total_registros_lake} registro(s) vinculados
        </span>
      </div>
      {data.note && (
        <p className="flex items-start gap-2 rounded-xl border border-amber-200/60 bg-amber-50/80 px-3 py-2.5 text-xs text-amber-900">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          {data.note}
        </p>
      )}

      <Card className="glass-card grid gap-3 p-5 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Número de caso" value={r.case_number} />
        <Field label="Tipo de delito" value={r.primary_type} />
        <Field label="Descripción" value={r.description} />
        <Field label="Fecha y hora" value={r.date} />
        <Field label="Distrito" value={r.district} />
        <Field label="Sector" value={r.beat} />
        <Field label="Zona" value={r.ward} />
        <Field label="Cuadra / bloque" value={r.block} />
        <Field label="Lugar del hecho" value={r.location_description} />
        <Field label="Código IUCR" value={r.iucr} />
        <Field label="Clasificación FBI" value={r.fbi_code} />
        <Field label="Año" value={r.year} />
        <Field label="Arresto" value={r.arrest} />
        <Field label="Violencia doméstica" value={r.domestic} />
        <Field label="Estado del expediente" value={r.estado_caso} />
        <Field label="Prioridad" value={r.prioridad_caso} />
        <Field label="Investigador asignado" value={r.investigador_asignado} />
      </Card>

      <Card className="glass-card flex flex-wrap items-start gap-4 p-5">
        <div className="rounded-xl bg-gradient-to-br from-indigo-600 to-blue-700 p-2.5 text-white shadow-md">
          <MapPin className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-900">Ubicación geográfica</p>
          <p className="mt-1 text-sm text-slate-600">
            Lat {r.latitude} · Lon {r.longitude}
          </p>
          <p className="mt-1 text-xs text-slate-500">{r.location}</p>
        </div>
      </Card>

      {data.hechos?.length > 1 && (
        <details className="glass-card rounded-xl p-4">
          <summary className="cursor-pointer text-sm font-medium text-slate-700 transition hover:text-indigo-600">
            Ver registros históricos ({data.hechos.length})
          </summary>
          <ul className="mt-3 max-h-48 space-y-2 overflow-y-auto text-xs text-slate-600">
            {data.hechos.map((h, i) => (
              <li key={i} className="rounded-lg border border-slate-100 bg-slate-50/80 px-3 py-2 font-mono">
                {h.primary_type} — {h.date} — {h.block}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}
