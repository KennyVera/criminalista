export function normalizeRole(user) {
  return String(user?.nombre_rol || '').toLowerCase().trim()
}

export function isAdmin(user) {
  return normalizeRole(user) === 'admin'
}

export function isComisario(user) {
  return normalizeRole(user) === 'comisario'
}

export function isAnalistaCriminal(user) {
  return normalizeRole(user) === 'analista criminal'
}

export function canViewDashboard(user) {
  const r = normalizeRole(user)
  return r === 'admin' || r === 'comisario' || r === 'analista criminal'
}

export function canViewOperationalIndicators(user) {
  const r = normalizeRole(user)
  return r === 'admin' || r === 'analista criminal'
}

export function canAccessDataCrud(user) {
  const r = normalizeRole(user)
  return r === 'admin' || r === 'analista criminal' || r === 'detective' || r === 'oficial'
}

export function canAccessAdmin(user) {
  return isAdmin(user)
}
