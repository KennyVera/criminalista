const DEFAULT_TTL_MS = 10 * 60 * 1000

function canUseStorage() {
  try {
    return typeof sessionStorage !== 'undefined'
  } catch {
    return false
  }
}

export function readSessionCache(key, ttlMs = DEFAULT_TTL_MS) {
  if (!canUseStorage()) return null
  try {
    const raw = sessionStorage.getItem(key)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!parsed?.savedAt || parsed.data === undefined) return null
    if (Date.now() - parsed.savedAt > ttlMs) {
      sessionStorage.removeItem(key)
      return null
    }
    return parsed.data
  } catch {
    return null
  }
}

export function writeSessionCache(key, data) {
  if (!canUseStorage()) return
  try {
    sessionStorage.setItem(key, JSON.stringify({ savedAt: Date.now(), data }))
  } catch {
    /* quota or private mode */
  }
}

export const CACHE_KEYS = {
  dashboardOverview: 'crimetrack:dashboard:overview',
  dashboardFilterOptions: 'crimetrack:dashboard:filter-options',
  dashboardFilteredEmpty: 'crimetrack:dashboard:filtered-empty',
  collections: 'crimetrack:collections',
}
