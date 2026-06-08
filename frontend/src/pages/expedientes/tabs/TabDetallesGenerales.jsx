import { useEffect, useState } from 'react'
import { MapPin } from 'lucide-react'
import { expedientesApi } from '../../../api/expedientes'
import { Card, Spinner } from '../../../components/ui'

function Field({ label, value }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="mt-0.5 text-sm text-slate-900">{value ?? '—'}</dd>
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
      <Card className="p-6 text-sm text-red-700">
        Error al consultar MinIO: {error}
      </Card>
    )
  }

  if (!data?.found) {
    return (
      <Card className="p-6 text-sm text-slate-600">
        {data?.message || 'Sin datos en el Data Lake para este expediente.'}
      </Card>
    )
  }

  const r = data.resumen || {}

  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-500">
        Origen: <span className="font-mono">{data.source}</span> ·{' '}
        {r.total_registros_lake} registro(s) asociados al número de caso
      </p>
      {data.note && (
        <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">{data.note}</p>
      )}

      <Card className="grid gap-4 p-6 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Número de caso" value={r.case_number} />
        <Field label="Tipo de crimen" value={r.primary_type} />
        <Field label="Descripción" value={r.description} />
        <Field label="Fecha / hora" value={r.date} />
        <Field label="Distrito" value={r.district} />
        <Field label="Beat" value={r.beat} />
        <Field label="Ward" value={r.ward} />
        <Field label="Bloque" value={r.block} />
        <Field label="Lugar" value={r.location_description} />
        <Field label="IUCR" value={r.iucr} />
        <Field label="Código FBI" value={r.fbi_code} />
        <Field label="Año" value={r.year} />
        <Field label="Arresto" value={r.arrest} />
        <Field label="Doméstico" value={r.domestic} />
        <Field label="Estado (expediente)" value={r.estado_caso} />
        <Field label="Prioridad" value={r.prioridad_caso} />
        <Field label="Investigador" value={r.investigador_asignado} />
      </Card>

      <Card className="flex flex-wrap items-start gap-4 p-6">
        <MapPin className="h-5 w-5 shrink-0 text-brand-600" />
        <div>
          <p className="text-sm font-semibold text-slate-900">Coordenadas</p>
          <p className="text-sm text-slate-600">
            Lat {r.latitude} · Lon {r.longitude}
          </p>
          <p className="mt-1 text-xs text-slate-500">{r.location}</p>
        </div>
      </Card>

      {data.hechos?.length > 1 && (
        <details className="rounded-xl border border-slate-200 bg-white p-4">
          <summary className="cursor-pointer text-sm font-medium text-slate-700">
            Ver todos los registros crudos ({data.hechos.length})
          </summary>
          <ul className="mt-3 max-h-48 space-y-2 overflow-y-auto text-xs text-slate-600">
            {data.hechos.map((h, i) => (
              <li key={i} className="rounded-lg bg-slate-50 p-2 font-mono">
                {h.primary_type} — {h.date} — {h.block}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}
