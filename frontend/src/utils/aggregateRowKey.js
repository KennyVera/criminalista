/** Clave estable para filas agregadas OLAP (evita duplicados distrito+beat). */
export function aggregateRowKey(row, index = 0) {
  return [
    row.distrito ?? row.district ?? '',
    row.beat ?? '',
    row.tipo ?? '',
    row.anio ?? '',
    row.mes ?? '',
    index,
  ].join('|')
}

/** Agrupa filas detalle en ranking por distrito/beat. */
export function rollupByDistrict(rows = []) {
  const map = new Map()
  for (const row of rows) {
    const district = row.distrito ?? row.district ?? '—'
    const beat = row.beat ?? ''
    const key = `${district}|${beat}`
    const prev = map.get(key) || { district, beat, total_crimes: 0 }
    prev.total_crimes += Number(row.total ?? row.total_crimes ?? 0)
    map.set(key, prev)
  }
  return [...map.values()].sort((a, b) => b.total_crimes - a.total_crimes)
}
