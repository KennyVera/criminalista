# Checklist — Nivel Operativo

> Validación verificable del nivel operativo (RV-01…RV-05).

## Cobertura y Trazabilidad

- [ ] Los 76 casos de uso CU-O01…CU-O60 **+ CU-O61…CU-O76 (NIVEL AUDITORÍA)** están especificados (detalle en `004/casos-uso.md`).
- [ ] Cada CU-O está mapeado a un paquete (P01–P12) y a un objetivo operativo (OP1–OP12).
- [ ] Cada CU-O traza a un OE (directo o como habilitador).
- [ ] Cada CU-O tiene una historia de usuario (HU-O-01…HU-O-60 **y HU-O-61…HU-O-76**).
- [ ] Cada CU-O tiene criterio de aceptación Dado/Cuando/Entonces.
- [ ] Los 16 CU nuevos de auditoría incluyen la estructura completa de 18 puntos (P03).

## Producto Criminalístico (P04–P08)

- [ ] Expedientes: crear/asignar/actualizar/vincular/cerrar con reglas (RN-09).
- [ ] Evidencias: registro, carga, hash y custodia íntegra (RS-07/RN-02).
- [ ] Involucrados: víctima/sospechoso/testigo vinculados a expedientes.
- [ ] Analítica: mapa de calor, indicadores, tendencias y predicción legibles (RI-04).
- [ ] Reportería: generación y exportación PDF/Excel auditada (RN-08).

## Negocio (P09–P12)

- [ ] Comercial B2G: leads, oportunidades, demos, RFP, propuestas.
- [ ] APIs: keys, documentación, webhooks, consumo, conectores (OE2).
- [ ] Cloud/SLA: uptime, backup, escalamiento, incidentes, DR (OE3).
- [ ] BI: consolidación, KPI, benchmark, tablero, forecast (OE4).

## Seguridad y Auditoría (P01–P03)

- [ ] Autenticación con MFA donde aplica (RS-04).
- [ ] Permisos validados en backend (RS-02).
- [ ] Toda operación sensible auditada y atribuible (RS-05/06).
- [ ] Alertas de manipulación y validación de cadena de custodia.
- [ ] **Auditoría total (NIVEL AUDITORÍA, CU-O61…O76):** CRUD, auth/sesiones, RBAC, acceso sensible,
  expedientes, evidencias/custodia, involucrados, exportaciones, configuración, APIs, cloud y BI.
- [ ] **Inmutabilidad append-only + hash encadenado + verificación de integridad** (CU-O75).
- [ ] **Tablero central y reportes de cumplimiento** solo para Auditor/Compliance (CU-O73/O74).
- [ ] **Retención/archivado** sin perder integridad (CU-O76); enmascaramiento; sin secretos en logs.
- [ ] Detalle de validación en `003-operativo/P03-auditoria/checklist.md`.

## Inmutables y Calidad

- [ ] No se modificó el alcance B2G (RN-03) ni OE1–OE4 (RN-04).
- [ ] Visualizaciones legibles y proporcionadas (RI-04).
- [ ] Aislamiento por tenant respetado (RN-06).

## Demostrabilidad en Video (RV-04)

- [ ] CU-O01, CU-O21, CU-O26, CU-O31, CU-O32, CU-O36, CU-O37, CU-O16 listos para demo (ver `005`).

## Pendientes

- [ ] Resolver PC-O1 (hash), PC-O2 (modelos predictivos/forecast), PC-O3 (retención).
- [ ] Resolver PC-O4 / PC-A1…PC-A6 (decisiones de auditoría: almacenamiento, tenant, retención, hash, parser UA, RBAC fino).
- [ ] Acta de aprobación (T-O-63).
