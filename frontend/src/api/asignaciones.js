import { api } from './client'

const B = '/packages/asignacion-investigaciones'

export const asignacionesApi = {
  detectivesDisponibles: () => api.request(`${B}/detectives-disponibles/`),
  casos: ({ q = '', page = 1, perPage = 40, soloSinAsignar = false, soloAsignados = false, estado = '', prioridad = '' } = {}) => {
    const params = new URLSearchParams()
    if (q) params.set('q', q)
    params.set('page', String(page))
    params.set('per_page', String(perPage))
    if (soloAsignados) params.set('asignados', '1')
    else if (soloSinAsignar) params.set('sin_asignar', '1')
    if (estado) params.set('estado', estado)
    if (prioridad) params.set('prioridad', prioridad)
    const qs = params.toString()
    return api.request(`${B}/casos/?${qs}`)
  },
  asignar: (body) =>
    api.request(`${B}/asignar/`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  reasignar: (fkCaso, body) =>
    api.request(`${B}/casos/${fkCaso}/reasignar/`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  remover: (fkCaso, body = {}) =>
    api.request(`${B}/casos/${fkCaso}/remover/`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  progreso: (misCasos = false) =>
    api.request(misCasos ? `${B}/progreso/?mis_casos=1` : `${B}/progreso/`),
}
