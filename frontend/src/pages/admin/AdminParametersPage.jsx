import { useEffect, useMemo, useState } from 'react'
import { Settings } from 'lucide-react'
import AdminGuard from '../../components/admin/AdminGuard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { adminApi } from '../../api/admin'
import { Button, Card } from '../../components/ui'
import { useAppConfig } from '../../context/AppConfigContext'
import { useToast } from '../../context/ToastContext'

const PARAM_DEFS = {
  app_nombre: {
    label: 'Nombre del aplicativo',
    tipo: 'string',
    descripcion: 'Nombre visible en la UI',
    placeholder: 'Ej. CrimeTrack Analytics',
  },
  registros_por_pagina: {
    label: 'Registros por páginas',
    tipo: 'int',
    descripcion: 'Paginación por defecto',
    placeholder: 'Ej. 25',
  },
  timezone: {
    label: 'Zona horaria',
    tipo: 'string',
    descripcion: 'Zona horaria del sistema',
    placeholder: 'Ej. America/Bogota',
  },
  app_subtitulo: {
    label: 'Subtítulo del aplicativo',
    tipo: 'string',
    descripcion: 'Texto secundario mostrado en encabezado',
    placeholder: 'Ej. Panel de analítica criminal — ISO 9241-210',
  },
  app_icon_url: {
    label: 'Logo del aplicativo (URL o base64)',
    tipo: 'string',
    descripcion: 'URL o data URL usada como icono del sistema',
    placeholder: 'https://.../logo.png o data:image/png;base64,...',
  },
}

export default function AdminParametersPage() {
  const [items, setItems] = useState([])
  const [draft, setDraft] = useState({})
  const [savingId, setSavingId] = useState(null)
  const { reloadConfig } = useAppConfig()
  const toast = useToast()

  const load = () =>
    adminApi.parametros().then((d) => {
      setItems(d.items || [])
      const o = {}
      ;(d.items || []).forEach((p) => {
        o[p.id_param] = p.valor
      })
      setDraft(o)
    })
  useEffect(() => {
    load()
  }, [])

  const mergedItems = useMemo(() => {
    const byKey = new Map(items.map((it) => [it.clave, it]))
    Object.entries(PARAM_DEFS).forEach(([clave, def]) => {
      if (!byKey.has(clave)) {
        byKey.set(clave, {
          id_param: `new:${clave}`,
          clave,
          valor: '',
          tipo: def.tipo,
          descripcion: def.descripcion,
          isNew: true,
        })
      }
    })
    return Array.from(byKey.values())
  }, [items])

  const save = async (id) => {
    const row = mergedItems.find((x) => x.id_param === id)
    if (!row) return
    setSavingId(id)
    try {
      if (row.isNew || String(id).startsWith('new:')) {
        await adminApi.createParametro({
          clave: row.clave,
          valor: draft[id] ?? '',
          tipo: PARAM_DEFS[row.clave]?.tipo || 'string',
          descripcion: PARAM_DEFS[row.clave]?.descripcion || row.descripcion || '',
        })
      } else {
        await adminApi.updateParametro(id, { valor: draft[id] })
      }
      await load()
      await reloadConfig()
      toast.success('Éxito', 'Parámetro guardado correctamente')
    } catch (err) {
      toast.error('Error', err.message || 'No se pudo guardar el parámetro')
    } finally {
      setSavingId(null)
    }
  }

  const handleLogoFile = async (id, file) => {
    if (!file) return
    const asDataUrl = await new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.onerror = reject
      reader.readAsDataURL(file)
    })
    setDraft((prev) => ({ ...prev, [id]: String(asDataUrl || '') }))
  }

  return (
    <AdminGuard>
      <AdminPageHeader
        title="Parámetros del sistema"
        subtitle="Configuración global de CrimeTrack Analytics"
        icon={Settings}
      />
      <Card className="space-y-4">
        {mergedItems.map((p) => (
          <div key={p.id_param} className="flex flex-wrap items-end gap-3 border-b pb-4">
            <div className="min-w-[200px] flex-1">
              <p className="font-medium text-slate-800">
                {PARAM_DEFS[p.clave]?.label || p.clave}
              </p>
              <p className="text-xs text-slate-500">{p.descripcion}</p>
            </div>
            <div className="flex min-w-[320px] flex-1 flex-col gap-2">
              <input
                value={draft[p.id_param] ?? ''}
                onChange={(e) => setDraft({ ...draft, [p.id_param]: e.target.value })}
                className="flex-1 rounded-xl border px-3 py-2 text-sm"
                placeholder={PARAM_DEFS[p.clave]?.placeholder || ''}
              />
              {p.clave === 'app_icon_url' && (
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleLogoFile(p.id_param, e.target.files?.[0])}
                    className="text-xs text-slate-600"
                  />
                  <span className="text-xs text-slate-500">
                    Puedes subir un logo o pegar la URL/manualmente.
                  </span>
                </div>
              )}
            </div>
            <Button
              type="button"
              variant="secondary"
              disabled={savingId === p.id_param}
              onClick={() => save(p.id_param)}
            >
              Guardar
            </Button>
          </div>
        ))}
      </Card>
    </AdminGuard>
  )
}
