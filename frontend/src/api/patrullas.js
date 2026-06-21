import { api } from './client'

const B = '/packages/asignacion-investigaciones'

const qs = (params = {}) => {
  const usable = Object.entries(params).filter(([, v]) => v !== '' && v != null)
  if (!usable.length) return ''
  return '?' + usable.map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&')
}

export const patrullasApi = {
  catalogos: () => api.request(`${B}/patrullas/catalogos/`),

  // CU-O77 — Comisario
  oficialesDisponibles: () => api.request(`${B}/patrullas/oficiales-disponibles/`),
  listar: (params) => api.request(`${B}/patrullas/${qs(params)}`),
  crear: (body) =>
    api.request(`${B}/patrullas/`, { method: 'POST', body: JSON.stringify(body) }),
  asignarOficiales: (id, body) =>
    api.request(`${B}/patrullas/${id}/oficiales/`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  removerOficial: (id, fkOficial) =>
    api.request(`${B}/patrullas/${id}/oficiales/${fkOficial}/`, { method: 'DELETE' }),

  // CU-O78 — Despacho (Comisario)
  listarIncidentes: (params) => api.request(`${B}/incidentes/${qs(params)}`),
  crearIncidente: (body) =>
    api.request(`${B}/incidentes/`, { method: 'POST', body: JSON.stringify(body) }),
  despachar: (id, body) =>
    api.request(`${B}/incidentes/${id}/despachar/`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  cerrarIncidente: (id) =>
    api.request(`${B}/incidentes/${id}/cerrar/`, { method: 'POST', body: '{}' }),
  devolverIncidente: (id, body) =>
    api.request(`${B}/incidentes/${id}/devolver/`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  // Oficial receptor
  misPatrullas: () => api.request(`${B}/mis-patrullas/`),
  avanzarIncidente: (id, body) =>
    api.request(`${B}/incidentes/${id}/avanzar/`, {
      method: 'POST',
      body: JSON.stringify(body || {}),
    }),
  finalizarIncidente: (id, body) =>
    api.request(`${B}/incidentes/${id}/finalizar/`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  solicitarApoyo: (id, body) =>
    api.request(`${B}/incidentes/${id}/apoyo/`, {
      method: 'POST',
      body: JSON.stringify(body || {}),
    }),
}
