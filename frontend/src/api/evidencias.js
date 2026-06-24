import { api } from './client'

const B = '/packages/evidencias'

export const evidenciasApi = {
  custodiaOpciones: () => api.request(`${B}/custodia/opciones/`),
  cambiarCustodia: (idEvidencia, body) =>
    api.request(`${B}/${idEvidencia}/custodia/`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  descargar: (idEvidencia, filename) =>
    api.downloadFile(`${B}/${idEvidencia}/descargar/`, filename),
  reproducirBlob: (idEvidencia) =>
    api.fetchBlob(`${B}/${idEvidencia}/descargar/?inline=1`),
  eliminar: (idEvidencia) =>
    api.request(`${B}/${idEvidencia}/`, { method: 'DELETE' }),
}
