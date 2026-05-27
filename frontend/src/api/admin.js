import { api } from './client'

const B = '/packages/administracion'

export const adminApi = {
  roles: () => api.request(`${B}/roles/`),
  users: () => api.request(`${B}/usuarios/`),
  createUser: (body) => api.request(`${B}/usuarios/`, { method: 'POST', body: JSON.stringify(body) }),
  getUser: (id) => api.request(`${B}/usuarios/${id}/`),
  updateUser: (id, body) =>
    api.request(`${B}/usuarios/${id}/`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteUser: (id) => api.request(`${B}/usuarios/${id}/`, { method: 'DELETE' }),
  setUserStatus: (id, activa) =>
    api.request(`${B}/usuarios/${id}/estado/`, {
      method: 'PATCH',
      body: JSON.stringify({ activa }),
    }),
  permisos: () => api.request(`${B}/permisos/`),
  rolPermisos: (fkRol) => api.request(`${B}/roles/${fkRol}/permisos/`),
  setRolPermisos: (fkRol, codigos) =>
    api.request(`${B}/roles/${fkRol}/permisos/`, {
      method: 'PUT',
      body: JSON.stringify({ codigos }),
    }),
  politicas: () => api.request(`${B}/politicas-seguridad/`),
  createPolitica: (body) =>
    api.request(`${B}/politicas-seguridad/`, { method: 'POST', body: JSON.stringify(body) }),
  updatePolitica: (id, body) =>
    api.request(`${B}/politicas-seguridad/${id}/`, { method: 'PATCH', body: JSON.stringify(body) }),
  parametros: () => api.request(`${B}/parametros/`),
  createParametro: (body) =>
    api.request(`${B}/parametros/`, { method: 'POST', body: JSON.stringify(body) }),
  updateParametro: (id, body) =>
    api.request(`${B}/parametros/${id}/`, { method: 'PATCH', body: JSON.stringify(body) }),
  respaldos: () => api.request(`${B}/respaldos/`),
  runRespaldo: () => api.request(`${B}/respaldos/`, { method: 'POST', body: '{}' }),
  updateRespaldo: (id, body) =>
    api.request(`${B}/respaldos/${id}/`, { method: 'PATCH', body: JSON.stringify(body) }),
  catalogos: () => api.request(`${B}/catalogos-delitos/`),
  createCatalogo: (body) =>
    api.request(`${B}/catalogos-delitos/`, { method: 'POST', body: JSON.stringify(body) }),
  updateCatalogo: (id, body) =>
    api.request(`${B}/catalogos-delitos/${id}/`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteCatalogo: (id) => api.request(`${B}/catalogos-delitos/${id}/`, { method: 'DELETE' }),
  zonas: () => api.request(`${B}/zonas-geograficas/`),
  createZona: (body) =>
    api.request(`${B}/zonas-geograficas/`, { method: 'POST', body: JSON.stringify(body) }),
  updateZona: (id, body) =>
    api.request(`${B}/zonas-geograficas/${id}/`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteZona: (id) => api.request(`${B}/zonas-geograficas/${id}/`, { method: 'DELETE' }),
  estadoSistema: () => api.request(`${B}/estado-sistema/`),
  seed: (reset = true) =>
    api.request(`${B}/seed/`, { method: 'POST', body: JSON.stringify({ reset }) }),
  publicConfig: () => api.request(`${B}/config-publica/`),
}
