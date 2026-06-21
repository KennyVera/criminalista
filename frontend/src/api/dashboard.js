import { api } from './client'

const B = '/packages/dashboard-analitica'

function buildQuery(params = {}) {
  const sp = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      sp.set(key, String(value))
    }
  })
  const q = sp.toString()
  return q ? `?${q}` : ''
}

export const dashboardApi = {
  overview: () => api.request(`${B}/overview/`),
  filtrosOpciones: () => api.request(`${B}/filtros/opciones/`),
  filtros: (params) => api.request(`${B}/filtros/${buildQuery(params)}`),
  mapaCalor: () => api.request(`${B}/mapa-calor/`),
  rankingDetectives: () => api.request(`${B}/ranking-detectives/`),
  indicadoresOperativos: () => api.request(`${B}/indicadores-operativos/`),
  prediccion: (params) => api.request(`${B}/prediccion/${buildQuery(params)}`),
}
