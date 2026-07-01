import { api } from './client'

const B = '/packages/administracion'

export const adminApi = {
  roles: () => api.request(`${B}/roles/`),
  users: () => api.request(`${B}/usuarios/`),
  createUser: (body) => api.request(`${B}/usuarios/`, { method: 'POST', body: JSON.stringify(body) }),
  generatePlaca: (fkRol) => api.request(`${B}/usuarios/generar-placa/?fk_rol=${fkRol}`),
  userFotoBlob: (id, version = '') =>
    api.fetchBlob(
      version
        ? `${B}/usuarios/${id}/foto/?v=${encodeURIComponent(version)}`
        : `${B}/usuarios/${id}/foto/`
    ),
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
  respaldos: (ejecutarPendientes = false) =>
    api.request(`${B}/respaldos/${ejecutarPendientes ? '?ejecutar_pendientes=1' : ''}`),
  respaldosHistorial: (limit = 50, manualOnly = false) =>
    api.request(`${B}/respaldos/historial/?limit=${limit}&manual_only=${manualOnly ? '1' : '0'}`),
  deleteRespaldoHistorial: (historialId) =>
    api.request(`${B}/respaldos/historial/${historialId}/`, { method: 'DELETE' }),
  deleteRespaldoHistorialBulk: (ids) =>
    api.request(`${B}/respaldos/historial/`, {
      method: 'POST',
      body: JSON.stringify({ accion: 'eliminar', ids }),
    }),
  respaldosAlertas: (hours = 72) =>
    api.request(`${B}/respaldos/alertas/?hours=${hours}`),
  respaldosProgramados: () =>
    api.request(`${B}/respaldos/programados/`, { method: 'POST', body: '{}' }),
  createRespaldoConfig: (body) =>
    api.request(`${B}/respaldos/`, {
      method: 'POST',
      body: JSON.stringify({ accion: 'config', ...body }),
    }),
  runRespaldo: (id) =>
    api.request(`${B}/respaldos/`, {
      method: 'POST',
      body: JSON.stringify({ id }),
    }),
  updateRespaldo: (id, body) =>
    api.request(`${B}/respaldos/${id}/`, { method: 'PATCH', body: JSON.stringify(body) }),
  downloadRespaldo: (historialId) =>
    api.downloadFile(
      `${B}/respaldos/historial/${historialId}/descargar/`,
      `crimetrack_respaldo_${historialId}.zip`
    ),
  restoreRespaldoZip: (file) => {
    const form = new FormData()
    form.append('archivo', file)
    return api.uploadForm(`${B}/respaldos/restaurar/`, form)
  },
  restoreRespaldoStatus: (taskId) => api.request(`${B}/respaldos/restaurar/estado/${taskId}/`),
  cancelRestoreRespaldo: (taskId) =>
    api.request(`${B}/respaldos/restaurar/cancelar/${taskId}/`, { method: 'POST' }),
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
