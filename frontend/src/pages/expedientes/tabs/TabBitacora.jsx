import { useCallback, useEffect, useState } from 'react'
import { expedientesApi } from '../../../api/expedientes'
import { Button, Card, Spinner } from '../../../components/ui'
import { useToast } from '../../../context/ToastContext'

const ESTADOS = ['Abierto', 'En investigación', 'Resuelto', 'Cerrado', 'Archivado']

export default function TabBitacora({ caseNumber, avanceInicial = 0, estadoInicial = 'En investigación' }) {
  const toast = useToast()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [nota, setNota] = useState('')
  const [avance, setAvance] = useState(avanceInicial)
  const [estado, setEstado] = useState(estadoInicial)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await expedientesApi.bitacora(caseNumber)
      setItems(res.items || [])
      if (res.items?.[0]) {
        setAvance(Number(res.items[0].avance_pct) || avance)
        setEstado(res.items[0].estado_caso || estado)
      }
    } catch (e) {
      toast.error('Error', e.message)
    } finally {
      setLoading(false)
    }
  }, [caseNumber, toast])

  useEffect(() => {
    load()
  }, [load])

  const submit = async (e) => {
    e.preventDefault()
    if (!nota.trim()) {
      toast.error('Nota requerida', 'Escriba el avance de la investigación')
      return
    }
    try {
      await expedientesApi.addBitacora(caseNumber, {
        nota,
        avance_pct: avance,
        estado_caso: estado,
      })
      toast.success('Registrado', 'Entrada agregada a la bitácora')
      setNota('')
      load()
    } catch (err) {
      toast.error('Error', err.message)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="p-4">
        <h3 className="mb-4 font-semibold text-slate-900">Línea de tiempo</h3>
        {loading ? (
          <Spinner />
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-500">Sin entradas en la bitácora.</p>
        ) : (
          <ol className="relative border-l-2 border-brand-200 pl-6">
            {items.map((entry) => (
              <li key={entry.id_bitacora} className="mb-6 last:mb-0">
                <span className="absolute -left-[7px] mt-1.5 h-3 w-3 rounded-full bg-brand-500" />
                <time className="text-xs text-slate-500">{entry.fecha_hora}</time>
                <p className="mt-1 text-sm font-medium text-slate-900">{entry.autor_nombre}</p>
                <p className="text-sm text-slate-700">{entry.nota}</p>
                <p className="mt-1 text-xs text-slate-500">
                  Avance {entry.avance_pct}% · {entry.estado_caso}
                </p>
              </li>
            ))}
          </ol>
        )}
      </Card>

      <Card className="p-4">
        <h3 className="mb-4 font-semibold text-slate-900">Registrar avance</h3>
        <form onSubmit={submit} className="space-y-4">
          <label className="block text-sm font-medium text-slate-700">
            Avance de investigación: {avance}%
            <input
              type="range"
              min={0}
              max={100}
              value={avance}
              onChange={(e) => setAvance(Number(e.target.value))}
              className="mt-2 w-full accent-brand-600"
            />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Estado del caso
            <select
              value={estado}
              onChange={(e) => setEstado(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2"
            >
              {ESTADOS.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Nota
            <textarea
              required
              value={nota}
              onChange={(e) => setNota(e.target.value)}
              rows={4}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2"
              placeholder="Diligencias realizadas, hallazgos, próximos pasos..."
            />
          </label>

          <Button type="submit">Agregar a bitácora</Button>
        </form>
      </Card>
    </div>
  )
}
