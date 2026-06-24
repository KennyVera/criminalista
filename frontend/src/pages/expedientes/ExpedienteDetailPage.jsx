import { useEffect, useState } from 'react'
import { Link, useParams, Navigate } from 'react-router-dom'
import { ArrowLeft, FileText, AlertCircle, Link2, MapPin } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { expedientesApi } from '../../api/expedientes'
import ExpedienteTabs from '../../components/expediente/ExpedienteTabs'
import TabDetallesGenerales from './tabs/TabDetallesGenerales'
import TabInvolucrados from './tabs/TabInvolucrados'
import TabEvidencias from './tabs/TabEvidencias'
import TabBitacora from './tabs/TabBitacora'
import { Spinner, Badge } from '../../components/ui'
import { canViewInvestigacionProgress, isOficial } from '../../utils/roles'

const ESTADO_EXP_TONE = {
  ACTIVO: 'green',
  REABIERTO: 'blue',
  CERRADO: 'warning',
  ARCHIVADO: 'neutral',
  ELIMINADO: 'danger',
}

export default function ExpedienteDetailPage() {
  const { numeroCaso } = useParams()
  const caseNumber = decodeURIComponent(numeroCaso || '')
  const { user } = useAuth()
  const [tab, setTab] = useState('general')
  const [cabecera, setCabecera] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [incidentes, setIncidentes] = useState([])

  // El Oficial puede abrir el detalle de los expedientes que registró
  // (el backend valida que sea el creador).
  const oficial = isOficial(user)
  const allowed = canViewInvestigacionProgress(user) || oficial
  // El Oficial hace el registro inicial (involucrados/evidencias preliminares)
  // pero NO registra avances de investigación (bitácora).
  const visibleTabs = oficial
    ? ['general', 'involucrados', 'evidencias']
    : ['general', 'involucrados', 'evidencias', 'bitacora']

  useEffect(() => {
    if (!allowed || !caseNumber) return
    setLoading(true)
    expedientesApi
      .cabecera(caseNumber)
      .then(setCabecera)
      .catch((e) =>
        setError(
          e.status === 403
            ? 'Acceso restringido: solo puede consultar y trabajar en los expedientes que el comisario le ha asignado.'
            : e.message,
        ),
      )
      .finally(() => setLoading(false))
    expedientesApi
      .incidentesVinculados(caseNumber)
      .then((res) => setIncidentes(res.items || []))
      .catch(() => setIncidentes([]))
  }, [caseNumber, allowed])

  if (!allowed) return <Navigate to="/" replace />

  if (!caseNumber) return <Navigate to="/expedientes" replace />

  return (
    <section className="mx-auto max-w-6xl space-y-6">
      <div className="glass-card rounded-xl p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link
              to="/expedientes"
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
            {cabecera?.expediente?.titulo && (
              <p className="mt-1 text-sm font-medium text-slate-600">
                {cabecera.expediente.titulo}
              </p>
            )}
            {cabecera && (
              <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-500">
                {cabecera.expediente?.estado && (
                  <>
                    <Badge tone={ESTADO_EXP_TONE[cabecera.expediente.estado] || 'neutral'}>
                      {cabecera.expediente.estado}
                    </Badge>
                    <span>·</span>
                  </>
                )}
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

      {incidentes.length > 0 && (
        <div className="glass-card rounded-xl p-5">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900">
            <Link2 className="h-4 w-4 text-indigo-600" />
            Incidentes vinculados
            <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-600">
              {incidentes.length}
            </span>
          </h3>
          <div className="grid gap-2 sm:grid-cols-2">
            {incidentes.map((inc) => (
              <div
                key={inc.id_incidente}
                className="rounded-lg border border-slate-200 bg-white/70 p-3 text-sm"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono font-semibold text-indigo-700">{inc.codigo}</span>
                  <Badge tone="neutral">{inc.estado}</Badge>
                </div>
                <p className="mt-1 font-medium text-slate-700">
                  {inc.tipo} · {inc.prioridad}
                </p>
                <p className="mt-0.5 flex items-center gap-1 text-xs text-slate-500">
                  <MapPin className="h-3 w-3" />
                  {(inc.fecha_reporte || '').slice(0, 10)} — {inc.ubicacion || 's/ubicación'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

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
        <ExpedienteTabs active={tab} onChange={setTab} tabs={visibleTabs}>
          {tab === 'general' && <TabDetallesGenerales caseNumber={caseNumber} />}
          {tab === 'involucrados' && <TabInvolucrados caseNumber={caseNumber} />}
          {tab === 'evidencias' && <TabEvidencias caseNumber={caseNumber} />}
          {!oficial && tab === 'bitacora' && (
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
