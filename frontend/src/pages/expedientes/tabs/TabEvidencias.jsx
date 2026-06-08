import { useCallback, useEffect, useState } from 'react'
import { Upload } from 'lucide-react'
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
      <Card className="p-4">
        <h3 className="mb-3 font-semibold text-slate-900">Custodia digital</h3>
        {loading ? (
          <Spinner />
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-500">Sin evidencias cargadas.</p>
        ) : (
          <ul className="space-y-2">
            {items.map((ev) => (
              <li
                key={ev.id_evidencia}
                className="rounded-xl border border-slate-100 px-3 py-2 text-sm"
              >
                <p className="font-medium text-slate-900">{ev.tipo_evidencia}</p>
                <p className="text-xs text-slate-500 break-all">{ev.minio_url}</p>
                <p className="text-xs text-slate-400">
                  {ev.peso_mb} MB · {ev.fecha_subida} · {ev.estado_custodia}
                </p>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card className="p-4">
        <h3 className="mb-3 flex items-center gap-2 font-semibold text-slate-900">
          <Upload className="h-4 w-4" />
          Subir evidencia
        </h3>
        <form onSubmit={upload} className="space-y-4">
          <input
            type="file"
            accept="image/*,video/*,audio/*,.pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-slate-600"
          />
          <Button type="submit" disabled={busy}>
            Subir a MinIO
          </Button>
        </form>
      </Card>
    </div>
  )
}
