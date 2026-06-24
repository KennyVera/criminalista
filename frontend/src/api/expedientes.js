import { api } from './client'

const B = '/packages/expedientes-criminales'

function enc(caseNumber) {
  return encodeURIComponent(caseNumber)
}

function qs(params = {}) {
  const sp = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') sp.set(k, String(v))
  })
  const s = sp.toString()
  return s ? `?${s}` : ''
}

export const expedientesApi = {
  catalogos: () => api.request(`${B}/catalogos/`),
  listar: (params = {}) => api.request(`${B}/${qs(params)}`),
  registrar: (body) =>
    api.request(`${B}/`, { method: 'POST', body: JSON.stringify(body) }),
  duplicados: (params = {}) => api.request(`${B}/duplicados/${qs(params)}`),
  buscarIncidentes: (params = {}) =>
    api.request(`${B}/incidentes-disponibles/${qs(params)}`),
  incidentesVinculados: (caseNumber) =>
    api.request(`${B}/${enc(caseNumber)}/incidentes/`),
  actualizar: (caseNumber, body) =>
    api.request(`${B}/${enc(caseNumber)}/editar/`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  cerrar: (caseNumber, motivo) =>
    api.request(`${B}/${enc(caseNumber)}/cerrar/`, {
      method: 'POST',
      body: JSON.stringify({ motivo }),
    }),
  reabrir: (caseNumber, motivo) =>
    api.request(`${B}/${enc(caseNumber)}/reabrir/`, {
      method: 'POST',
      body: JSON.stringify({ motivo }),
    }),
  archivar: (caseNumber, motivo) =>
    api.request(`${B}/${enc(caseNumber)}/archivar/`, {
      method: 'POST',
      body: JSON.stringify({ motivo }),
    }),
  eliminar: (caseNumber, motivo) =>
    api.request(`${B}/${enc(caseNumber)}/eliminar/`, {
      method: 'DELETE',
      body: JSON.stringify({ motivo }),
    }),
  cabecera: (caseNumber) => api.request(`${B}/${enc(caseNumber)}/`),
  detallesGenerales: (caseNumber) =>
    api.request(`${B}/${enc(caseNumber)}/detalles-generales/`),
  involucrados: (caseNumber) => api.request(`${B}/${enc(caseNumber)}/involucrados/`),
  addInvolucrado: (caseNumber, body) =>
    api.request(`${B}/${enc(caseNumber)}/involucrados/`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  addInvolucradoMultipart: (caseNumber, formData) =>
    api.uploadForm(`${B}/${enc(caseNumber)}/involucrados/`, formData),
  evidencias: (caseNumber) => api.request(`${B}/${enc(caseNumber)}/evidencias/`),
  uploadEvidencia: (caseNumber, formData) =>
    api.uploadForm(`${B}/${enc(caseNumber)}/evidencias/`, formData),
  bitacora: (caseNumber) => api.request(`${B}/${enc(caseNumber)}/bitacora/`),
  cierreRequisitos: (caseNumber) =>
    api.request(`${B}/${enc(caseNumber)}/cierre/requisitos/`),
  addBitacora: (caseNumber, body) =>
    api.request(`${B}/${enc(caseNumber)}/bitacora/`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  downloadInformePdf: (caseNumber) =>
    api.downloadFile(
      `${B}/${enc(caseNumber)}/informe-pdf/`,
      `Informe_Penal_${caseNumber}.pdf`
    ),
}
