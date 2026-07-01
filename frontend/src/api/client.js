const BASE = '/api'

let authToken = null

function buildQuery(params = {}) {
  const sp = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      sp.set(key, String(value))
    }
  })
  return sp.toString()
}

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`
  }
  const res = await fetch(`${BASE}${path}`, {
    headers,
    ...options,
  })
  if (res.status === 204) return null
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = data.error || data.message || res.statusText
    const err = new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    err.code = data.code
    err.status = res.status
    if (data.code === 'SESSION_REVOKED' && data.message) {
      err.message = data.message
    }
    throw err
  }
  return data
}

function requestLong(path, options = {}, timeoutMs = 600000) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  return request(path, { ...options, signal: controller.signal }).finally(() =>
    clearTimeout(timer)
  )
}

async function uploadForm(path, formData) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    body: formData,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.error || data.message || res.statusText)
  }
  return data
}

async function fetchBlob(path) {
  const res = await fetch(`${BASE}${path}`, {
    headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    cache: 'no-store',
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    const err = new Error(data.detail || data.error || res.statusText)
    err.status = res.status
    throw err
  }
  const blob = await res.blob()
  return { blob, contentType: res.headers.get('Content-Type') || blob.type }
}

async function downloadFile(path, filename) {
  const res = await fetch(`${BASE}${path}`, {
    headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error || res.statusText)
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename || 'descarga.zip'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export const api = {
  request,
  downloadFile,
  fetchBlob,
  uploadForm,
  setAuthToken: (token) => {
    authToken = token
  },
  authLogin: (email, password) =>
    request('/packages/autenticacion/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  authVerifyMfa: (email, code) =>
    request('/packages/autenticacion/mfa/verificar/', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    }),
  authResendMfa: (email) =>
    request('/packages/autenticacion/mfa/reenviar/', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
  authLogout: () =>
    request('/packages/autenticacion/logout/', { method: 'POST' }),
  authChangePassword: (current_password, new_password) =>
    request('/packages/autenticacion/cambiar-contrasena/', {
      method: 'POST',
      body: JSON.stringify({ current_password, new_password }),
    }),
  authProfile: () => request('/packages/autenticacion/perfil/'),
  authUpdateProfile: (body) =>
    request('/packages/autenticacion/perfil/', {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  authUploadProfileFoto: (formData) =>
    uploadForm('/packages/autenticacion/perfil/foto/', formData),
  authProfileFotoBlob: (version = '') =>
    fetchBlob(
      version
        ? `/packages/autenticacion/perfil/foto/?v=${encodeURIComponent(version)}`
        : '/packages/autenticacion/perfil/foto/'
    ),
  authRemoveProfileFoto: () =>
    request('/packages/autenticacion/perfil/foto/', { method: 'DELETE' }),
  authMe: () => request('/packages/autenticacion/me/'),
  authActiveSessions: () => request('/packages/autenticacion/sesiones-activas/'),
  authCloseSession: (idSesion) =>
    request(`/packages/autenticacion/sesiones-activas/${idSesion}/cerrar/`, {
      method: 'POST',
    }),
  authSessionStatus: () => request('/packages/autenticacion/sesion-estado/'),
  authRequestPasswordReset: (email) =>
    request('/packages/autenticacion/recuperar-contrasena/', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
  authResetPassword: (email, code, new_password) =>
    request('/packages/autenticacion/restablecer-contrasena/', {
      method: 'POST',
      body: JSON.stringify({ email, code, new_password }),
    }),
  listPackages: () => request('/packages/'),
  health: () => request('/health/'),
  dashboard: () => request('/packages/dashboard-analitica/overview/'),
  collections: () => request('/meta/collections/'),
  collectionMeta: (slug) => request(`/meta/collections/${slug}/`),
  listRecords: (slug, params = {}) => {
    const q = buildQuery(params)
    const path = `/collections/${slug}/records/`
    return request(q ? `${path}?${q}` : path)
  },
  getRecord: (slug, id, expand) => {
    const q = expand ? `?expand=${encodeURIComponent(expand)}` : ''
    return request(`/collections/${slug}/records/${id}/${q}`)
  },
  createRecord: (slug, body) =>
    request(`/collections/${slug}/records/`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  updateRecord: (slug, id, body) =>
    request(`/collections/${slug}/records/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  deleteRecord: (slug, id) =>
    request(`/collections/${slug}/records/${id}/`, { method: 'DELETE' }),
  relationOptions: (slug) => request(`/collections/${slug}/options/`),
  syncPocketBaseStats: () => request('/sync/pocketbase/stats/'),
  syncPocketBase: ({ mode = 'auto', export_raw_copy = true, cantidad_registros } = {}) =>
    request('/sync/pocketbase/', {
      method: 'POST',
      body: JSON.stringify({
        mode,
        export_raw_copy,
        ...(cantidad_registros != null ? { cantidad_registros } : {}),
      }),
    }),
  runEtlToMinioAsync: () =>
    request('/sync/pocketbase/', {
      method: 'POST',
      body: JSON.stringify({ mode: 'auto', export_raw_copy: true }),
    }),
  etlTaskStatus: (taskId) => request(`/etl/status/${taskId}/`),
  jobStatus: (taskId) => request(`/jobs/status/${taskId}/`),
  etlStatus: (taskId) => request(`/etl-status/${taskId}/`),
  runEtlToMinio: () =>
    requestLong('/etl/pb-to-minio/', {
      method: 'POST',
      body: JSON.stringify({ export_raw_copy: true }),
    }),
}
