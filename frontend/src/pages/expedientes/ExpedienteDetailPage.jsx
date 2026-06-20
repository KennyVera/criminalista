import { useEffect, useState } from 'react'
import { Link, useParams, Navigate } from 'react-router-dom'
import { ArrowLeft, FileText, AlertCircle } from 'lucide-react'
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
      <div className="glass-card rounded-xl p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link
              to="/investigaciones/progreso"
              className="mb-3 inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-sm font-medium text-indigo-600 transition hover:bg-indigo-50 hover:text-indigo-700"
            >
              <ArrowLeft className="h-4 w-4" />
              Volver a expedientes
            </Link>
            <h2 className="flex items-center gap-3 text-2xl font-bold tracking-tight text-slate-900">
              <span className="rounded-xl bg-gradient-to-br from-indigo-600 to-blue-700 p-2 text-white shadow-md">
                <FileText className="h-5 w-5" />
              </span>
              Expediente {caseNumber}
            </h2>
            {cabecera && (
              <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-500">
                <span className="status-badge status-badge--neutral">
                  {cabecera.estado_caso || 'Sin estado'}
                </span>
                <span>·</span>
                <span>Avance {cabecera.avance_pct ?? 0}%</span>
                {cabecera.asignacion?.detective_nombre && (
                  <>
                    <span>·</span>
                    <span>{cabecera.asignacion.detective_nombre}</span>
                  </>
                )}
              </div>
            )}
          </div>
          {cabecera?.dim_caso?.prioridad_caso && (
            <Badge tone="blue">{cabecera.dim_caso.prioridad_caso}</Badge>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Spinner />
        </div>
      ) : error ? (
        <div className="flex items-start gap-3 rounded-xl border border-red-200/80 bg-red-50/80 p-4 text-sm text-red-800 shadow-sm">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
          <p>{error}</p>
        </div>
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
