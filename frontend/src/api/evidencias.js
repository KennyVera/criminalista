import { api } from './client'

const B = '/packages/evidencias'

export const evidenciasApi = {
  custodiaOpciones: () => api.request(`${B}/custodia/opciones/`),
  cambiarCustodia: (idEvidencia, body) =>
    api.request(`${B}/${idEvidencia}/custodia/`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}
