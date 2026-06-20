export const EMPTY_DASHBOARD_FILTERS = { zona: '', tipo: '', fecha: '' }

/** Convierte YYYY-MM del input type="month" a parámetros anio/mes del API. */
export function dashboardFiltersToApi(draft = {}) {
  const params = {}
  if (draft.zona) params.zona = draft.zona
  if (draft.tipo) params.tipo = draft.tipo
  if (draft.fecha) {
    const [anio, mesPart] = String(draft.fecha).split('-')
    if (anio) params.anio = anio
    if (mesPart) params.mes = String(Number(mesPart))
  }
  return params
}

export function hasDashboardFilters(draft = {}) {
  return Boolean(draft.zona || draft.tipo || draft.fecha)
}
