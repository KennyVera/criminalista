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

export function isDetective(user) {
  return normalizeRole(user) === 'detective'
}

export function canManageAsignaciones(user) {
  const r = normalizeRole(user)
  return r === 'comisario' || r === 'admin'
}

export function canViewInvestigacionProgress(user) {
  const r = normalizeRole(user)
  return r === 'comisario' || r === 'detective' || r === 'admin'
}

export function isOficial(user) {
  return normalizeRole(user) === 'oficial'
}

export function canManagePatrullas(user) {
  const r = normalizeRole(user)
  return r === 'comisario' || r === 'admin'
}

// Solo el Comisario (y Admin) despacha y supervisa el cierre.
export function canDespachar(user) {
  const r = normalizeRole(user)
  return r === 'comisario' || r === 'admin'
}
