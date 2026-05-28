import { api } from './client'

const B = '/packages/administracion/recuperacion'

export const recoveryApi = {
  estado: () => api.request(`${B}/estado/`),
  login: (email, password) =>
    api.request(`${B}/login/`, {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  historial: () => api.request(`${B}/historial/`),
  restaurar: (file) => {
    const form = new FormData()
    form.append('archivo', file)
    return api.uploadForm(`${B}/restaurar/`, form)
  },
  restaurarEstado: (taskId) => api.request(`${B}/restaurar/estado/${taskId}/`),
  cancelarRestaurar: (taskId) =>
    api.request(`${B}/restaurar/cancelar/${taskId}/`, { method: 'POST' }),
  download: (historialId) =>
    api.downloadFile(
      `${B}/historial/${historialId}/descargar/`,
      `crimetrack_respaldo_${historialId}.zip`
    ),
}
