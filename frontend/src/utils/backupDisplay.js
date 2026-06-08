/** Tablas lógicas Parquet en respaldo completo (11 TX + 8 admin). */
export const TX_TABLES_COMPLETO = 11
export const ADMIN_TABLES_COMPLETO = 8
export const LOGICAL_TABLES_COMPLETO = TX_TABLES_COMPLETO + ADMIN_TABLES_COMPLETO

/** Respaldos anteriores a incluir asignaciones/bitácora/casos operativos. */
export const LOGICAL_TABLES_COMPLETO_LEGACY = 16

/** Muestra el conteo guardado en historial (16 legacy, 19 actuales). */
export function displayTablasCount(count) {
  const n = Number(count) || 0
  if (n <= 0) return '—'
  // Conteos inflados viejos (sumaban cada parquet OLAP como "tabla")
  if (n > 30) return LOGICAL_TABLES_COMPLETO_LEGACY
  return n
}

/** Normaliza detalle de historial; no altera registros con 16 tablas legacy. */
export function formatBackupEstado(text) {
  if (!text) return '—'
  let out = String(text)
  out = out.replace(/OK — (\d+) tablas/i, (full, num) => {
    const n = parseInt(num, 10)
    if (n > 30) return `OK — ${LOGICAL_TABLES_COMPLETO_LEGACY} tablas`
    return full
  })
  return out
}
