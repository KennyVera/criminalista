import { useCallback, useEffect, useState } from 'react'
import { Upload, Fingerprint, FileArchive } from 'lucide-react'
import { expedientesApi } from '../../../api/expedientes'
import { Button, Card, Spinner } from '../../../components/ui'
import { useToast } from '../../../context/ToastContext'

export default function TabEvidencias({ caseNumber }) {
  const toast = useToast()
  const [items, setItems] = useState([])
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
      toast.success('Subido', 'Evidencia guardada en MinIO')
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
              <li
                key={ev.id_evidencia}
                className="rounded-xl border border-slate-200/70 bg-white/60 px-4 py-3 text-sm shadow-sm"
              >
                <div className="flex items-center gap-2">
                  <FileArchive className="h-4 w-4 text-indigo-500" />
                  <p className="font-semibold text-slate-900">{ev.tipo_evidencia}</p>
                </div>
                <p className="mt-1 break-all text-xs text-slate-500">{ev.minio_url}</p>
                <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-400">
                  <span className="status-badge status-badge--neutral">{ev.peso_mb} MB</span>
                  <span>{ev.fecha_subida}</span>
                  <span className="status-badge status-badge--active">{ev.estado_custodia}</span>
                </div>
              </li>
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
          <Button type="submit" disabled={busy}>
            <Upload className="h-4 w-4" />
            Subir evidencia
          </Button>
        </form>
      </Card>
    </div>
  )
}
