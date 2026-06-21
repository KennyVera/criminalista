import { api } from './client'

const B = '/packages/reporteria'

export const reporteriaApi = {
  opciones: () => api.request(`${B}/opciones/`),
  enviar: (body) =>
    api.request(`${B}/enviar/`, { method: 'POST', body: JSON.stringify(body) }),
  programados: () => api.request(`${B}/programados/`),
  crearProgramado: (body) =>
    api.request(`${B}/programados/`, { method: 'POST', body: JSON.stringify(body) }),
  actualizarProgramado: (id, body) =>
    api.request(`${B}/programados/${id}/`, { method: 'PATCH', body: JSON.stringify(body) }),
  eliminarProgramado: (id) =>
    api.request(`${B}/programados/${id}/`, { method: 'DELETE' }),
}
