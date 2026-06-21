import { api } from './client'

const B = '/packages/auditoria'

function qs(params = {}) {
  const sp = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') sp.set(k, String(v))
  })
  const s = sp.toString()
  return s ? `?${s}` : ''
}

export const auditoriaApi = {
  eventos: (params = {}) => api.request(`${B}/eventos/${qs(params)}`),
  exportarCsv: (params = {}) => {
    const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '')
    return api.downloadFile(`${B}/eventos/exportar/${qs(params)}`, `auditoria_${stamp}.csv`)
  },
  verificarIntegridad: () => api.request(`${B}/integridad/`),
  verificarCustodia: () => api.request(`${B}/custodia/`),
}
