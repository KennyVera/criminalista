import { useEffect, useState } from 'react'
import { Link, useParams, Navigate } from 'react-router-dom'
import { ArrowLeft, FileText } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { expedientesApi } from '../../api/expedientes'
import ExpedienteTabs from '../../components/expediente/ExpedienteTabs'
import TabDetallesGenerales from './tabs/TabDetallesGenerales'
import TabInvolucrados from './tabs/TabInvolucrados'
import TabEvidencias from './tabs/TabEvidencias'
import TabBitacora from './tabs/TabBitacora'
import { Spinner, Badge } from '../../components/ui'
import { canViewInvestigacionProgress } from '../../utils/roles'

export default function ExpedienteDetailPage() {
  const { numeroCaso } = useParams()
  const caseNumber = decodeURIComponent(numeroCaso || '')
  const { user } = useAuth()
  const [tab, setTab] = useState('general')
  const [cabecera, setCabecera] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const allowed = canViewInvestigacionProgress(user)

  useEffect(() => {
    if (!allowed || !caseNumber) return
    setLoading(true)
    expedientesApi
      .cabecera(caseNumber)
      .then(setCabecera)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [caseNumber, allowed])

  if (!allowed) return <Navigate to="/" replace />

  if (!caseNumber) return <Navigate to="/investigaciones/progreso" replace />

  return (
    <section className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link
            to="/investigaciones/progreso"
            className="mb-2 inline-flex items-center gap-1 text-sm text-brand-600 hover:underline"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver a expedientes
          </Link>
          <h2 className="flex items-center gap-2 text-xl font-bold text-slate-900">
            <FileText className="h-6 w-6 text-brand-600" />
            Expediente {caseNumber}
          </h2>
          {cabecera && (
            <p className="mt-1 text-sm text-slate-500">
              Estado: {cabecera.estado_caso || '—'} · Avance {cabecera.avance_pct ?? 0}%
              {cabecera.asignacion?.detective_nombre && (
                <> · {cabecera.asignacion.detective_nombre}</>
              )}
            </p>
          )}
        </div>
        {cabecera?.dim_caso?.prioridad_caso && (
          <Badge tone="blue">{cabecera.dim_caso.prioridad_caso}</Badge>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Spinner />
        </div>
      ) : error ? (
        <p className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</p>
      ) : (
        <ExpedienteTabs active={tab} onChange={setTab}>
          {tab === 'general' && <TabDetallesGenerales caseNumber={caseNumber} />}
          {tab === 'involucrados' && <TabInvolucrados caseNumber={caseNumber} />}
          {tab === 'evidencias' && <TabEvidencias caseNumber={caseNumber} />}
          {tab === 'bitacora' && (
            <TabBitacora
              caseNumber={caseNumber}
              avanceInicial={cabecera?.avance_pct ?? 0}
              estadoInicial={cabecera?.estado_caso || 'En investigación'}
            />
          )}
        </ExpedienteTabs>
      )}
    </section>
  )
}
