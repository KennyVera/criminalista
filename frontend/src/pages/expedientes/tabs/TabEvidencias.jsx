import { useCallback, useEffect, useState } from 'react'
import { Upload, Fingerprint, FileArchive, ShieldCheck, Hash } from 'lucide-react'
import { expedientesApi } from '../../../api/expedientes'
import { evidenciasApi } from '../../../api/evidencias'
import { Button, Card, Spinner } from '../../../components/ui'
import { useToast } from '../../../context/ToastContext'

const CUSTODY_BADGE = {
  'En custodia': 'status-badge--active',
  'En análisis': 'status-badge--info',
  Transferida: 'status-badge--warning',
  Liberada: 'status-badge--neutral',
  Destruida: 'status-badge--danger',
}

function custodyBadgeClass(estado) {
  return CUSTODY_BADGE[estado] || 'status-badge--neutral'
}

function EvidenceItem({ ev, transiciones, onChanged }) {
  const toast = useToast()
  const opciones = transiciones[ev.estado_custodia] || []
  const [target, setTarget] = useState('')
  const [motivo, setMotivo] = useState('')
  const [saving, setSaving] = useState(false)

  const apply = async () => {
    if (!target) {
      toast.error('Seleccione un estado', 'Elija el nuevo estado de custodia')
      return
    }
    setSaving(true)
    try {
      await evidenciasApi.cambiarCustodia(ev.id_evidencia, { estado: target, motivo })
      toast.success('Custodia actualizada', `Evidencia #${ev.id_evidencia} → ${target}`)
      setTarget('')
      setMotivo('')
      onChanged()
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setSaving(false)
    }
  }

  const hash = String(ev.hash_sha256 || '')

  return (
    <li className="rounded-xl border border-slate-200/70 bg-white/60 px-4 py-3 text-sm shadow-sm">
      <div className="flex items-center gap-2">
        <FileArchive className="h-4 w-4 text-indigo-500" />
        <p className="font-semibold text-slate-900">
          {ev.nombre_archivo || ev.tipo_evidencia}
        </p>
        <span className={`status-badge ${custodyBadgeClass(ev.estado_custodia)} ml-auto`}>
          {ev.estado_custodia}
        </span>
      </div>

      <p className="mt-1 break-all text-xs text-slate-500">{ev.minio_url}</p>

      {hash && (
        <div
          className="mt-2 flex items-center gap-1.5 text-xs text-slate-500"
          title={`${ev.algoritmo_hash || 'SHA-256'}: ${hash}`}
        >
          <Hash className="h-3.5 w-3.5 text-emerald-600" />
          <span className="font-medium text-slate-600">{ev.algoritmo_hash || 'SHA-256'}</span>
          <code className="break-all font-mono text-[11px] text-slate-500">
            {hash.slice(0, 24)}…{hash.slice(-8)}
          </code>
        </div>
      )}

      <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-400">
        <span className="status-badge status-badge--neutral">{ev.peso_mb} MB</span>
        <span>{ev.tipo_evidencia}</span>
        <span>{ev.fecha_subida}</span>
      </div>

      {opciones.length > 0 ? (
        <div className="mt-3 flex flex-wrap items-end gap-2 border-t border-slate-100 pt-3">
          <label className="flex-1 min-w-[140px]">
            <span className="mb-1 block text-[11px] font-medium text-slate-500">
              Nuevo estado
            </span>
            <select
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs font-medium text-black"
            >
              <option value="">Seleccionar…</option>
              {opciones.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </label>
          <label className="flex-[2] min-w-[160px]">
            <span className="mb-1 block text-[11px] font-medium text-slate-500">
              Motivo (opcional)
            </span>
            <input
              type="text"
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              placeholder="Ej. Enviada a laboratorio"
              className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-black"
            />
          </label>
          <Button type="button" size="sm" onClick={apply} disabled={saving}>
            {saving ? <Spinner size="sm" /> : <ShieldCheck className="h-3.5 w-3.5" />}
            Cambiar
          </Button>
        </div>
      ) : (
        <p className="mt-2 text-[11px] italic text-slate-400">
          Estado terminal — sin transiciones disponibles.
        </p>
      )}
    </li>
  )
}

export default function TabEvidencias({ caseNumber }) {
  const toast = useToast()
  const [items, setItems] = useState([])
  const [transiciones, setTransiciones] = useState({})
  const [loading, setLoading] = useState(true)
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await expedientesApi.evidencias(caseNumber)
      setItems(res.items || [])
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setLoading(false)
    }
  }, [caseNumber, toast])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    evidenciasApi
      .custodiaOpciones()
      .then((res) => setTransiciones(res.transiciones || {}))
      .catch(() => setTransiciones({}))
  }, [])

  const upload = async (e) => {
    e.preventDefault()
    if (!file) {
      toast.error('Archivo requerido', 'Seleccione un archivo multimedia')
      return
    }
    setBusy(true)
    const fd = new FormData()
    fd.append('archivo', file)
    fd.append('tipo_evidencia', 'Multimedia')
    try {
      await expedientesApi.uploadEvidencia(caseNumber, fd)
      toast.success('Subido', 'Evidencia guardada con hash SHA-256')
      setFile(null)
      load()
    } catch (err) {
      toast.error('Error', err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="glass-card p-5">
        <div className="mb-4 flex items-center gap-2">
          <Fingerprint className="h-5 w-5 text-indigo-600" />
          <h3 className="font-semibold text-slate-900">Cadena de custodia digital</h3>
        </div>
        {loading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : items.length === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 px-4 py-8 text-center text-sm text-slate-500">
            No hay evidencias cargadas para este expediente.
          </p>
        ) : (
          <ul className="space-y-2.5">
            {items.map((ev) => (
              <EvidenceItem
                key={ev.id_evidencia}
                ev={ev}
                transiciones={transiciones}
                onChanged={load}
              />
            ))}
          </ul>
        )}
      </Card>

      <Card className="glass-card p-5">
        <h3 className="mb-4 flex items-center gap-2 font-semibold text-slate-900">
          <Upload className="h-5 w-5 text-indigo-600" />
          Cargar evidencia
        </h3>
        <form onSubmit={upload} className="space-y-4">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">
              Archivo multimedia
            </span>
            <div className="rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/50 px-4 py-6 text-center transition hover:border-indigo-300 hover:bg-indigo-50/30">
              <input
                type="file"
                accept="image/*,video/*,audio/*,.pdf"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="block w-full cursor-pointer text-sm text-slate-600 file:mr-4 file:cursor-pointer file:rounded-lg file:border-0 file:bg-indigo-600 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-indigo-700"
              />
              {file && (
                <p className="mt-2 text-xs font-medium text-indigo-600">{file.name}</p>
              )}
            </div>
          </label>
          <p className="text-xs text-slate-500">
            Al subir se calcula automáticamente el hash SHA-256 para garantizar la integridad.
          </p>
          <Button type="submit" disabled={busy}>
            <Upload className="h-4 w-4" />
            Subir evidencia
          </Button>
        </form>
      </Card>
    </div>
  )
}
