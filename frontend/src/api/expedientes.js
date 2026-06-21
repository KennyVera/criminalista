import { api } from './client'

const B = '/packages/expedientes-criminales'

function enc(caseNumber) {
  return encodeURIComponent(caseNumber)
}

export const expedientesApi = {
  cabecera: (caseNumber) => api.request(`${B}/${enc(caseNumber)}/`),
  detallesGenerales: (caseNumber) =>
    api.request(`${B}/${enc(caseNumber)}/detalles-generales/`),
  involucrados: (caseNumber) => api.request(`${B}/${enc(caseNumber)}/involucrados/`),
  addInvolucrado: (caseNumber, body) =>
    api.request(`${B}/${enc(caseNumber)}/involucrados/`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
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
