# Lista de Tareas — P03 Auditoría y Trazabilidad (AMPLIACIÓN)

> **CASOS DE USO NUEVOS — NIVEL AUDITORÍA.** Tareas trazables a CU-O61…CU-O76 y a los CU existentes
> CU-O11…CU-O15. **No ejecutar hasta aprobación de la especificación.** `[ ]` pendiente.

## Etapa 0 — Aprobación / decisiones
- [ ] T-00.1 Validar `spec.md` con el negocio/seguridad.
- [ ] T-00.2 Resolver PC-A1 almacenamiento (PostgreSQL append-only vs MinIO WORM).
- [ ] T-00.3 Resolver PC-A2..PC-A6 (tenant, retención, hash, parser UA, RBAC fino).

## Etapa 1 — Núcleo (CU-O61, CU-O62)
- [ ] T-01.1 Definir esquema `audit_events` + `audit_event_changes` + `audit_sessions`.
- [ ] T-01.2 Implementar `AuditService.record()` (normalización, enmascarado, hash + previous_hash).
- [ ] T-01.3 Implementar `AuditMiddleware` (contexto request: IP, UA→nav/SO/disp, endpoint, método, código, duración, correlation/trace, sesión).
- [ ] T-01.4 Implementar decorador `@audited(accion, entidad, tipo_operacion)` (antes/después + diff).
- [ ] T-01.5 Escritura asíncrona (Celery) + buffer/reintento + alerta ante fallo.
- [ ] T-01.6 Extender `AuthService` (MFA/bloqueos/cierre/duración/sesiones simultáneas).

## Etapa 2 — Cobertura por dominio
- [ ] T-02.1 (CU-O63) Auditar roles/permisos/privilegios + accesos denegados + rol efectivo.
- [ ] T-02.2 (CU-O64) Helpers `audit_access` para info sensible (modos: consulta/descarga/exportación…).
- [ ] T-02.3 (CU-O65) Auditar expedientes (creación, estado, reasignación, cierre, reapertura, historial).
- [ ] T-02.4 (CU-O67) Auditar involucrados (víctimas/sospechosos/testigos, confidencialidad).
- [ ] T-02.5 (CU-O66) Calcular **hash de evidencia** + `audit_evidence_events` + `audit_custody_events` (habilita CU-O15).

## Etapa 3 — Exportaciones / admin / APIs / cloud / BI
- [ ] T-03.1 (CU-O68) Auditar reportes/exportaciones (`audit_exports`, formato, marca de agua, motivo, destinatarios).
- [ ] T-03.2 (CU-O69) Auditar administración/configuración (catálogos, parámetros, instituciones, módulos, licencias, SLA, retención).
- [ ] T-03.3 (CU-O70) Auditar APIs/integraciones (`audit_api_events`, webhooks, **sin secretos completos**).
- [ ] T-03.4 (CU-O71) Auditar cloud/continuidad (backups/restore/DR/SLA/RTO/RPO).
- [ ] T-03.5 (CU-O72) Auditar analítica/BI/IA (dashboards, KPIs, modelos, datasets, versiones).

## Etapa 4 — Integridad / retención / alertas
- [ ] T-04.1 (CU-O75) Job de verificación de integridad (Celery beat) + `audit_integrity_checks` + notificación.
- [ ] T-04.2 (CU-O76) Políticas de retención + archivado (`audit_retention_policies`, `audit_archives`), suspensión por investigación.
- [ ] T-04.3 (FASE 5 / CU-O14) Motor de alertas → `audit_security_alerts` con campos (tipo, severidad, responsable, acción, cierre).

## Etapa 5 — API de consulta (CU-O73, CU-O74)
- [ ] T-05.1 Implementar `auditoria_trazabilidad/views.py` + `urls.py` (registrar paquete como implementado).
- [ ] T-05.2 (CU-O73) Endpoint tablero/búsqueda con filtros avanzados + línea de tiempo + antes/después.
- [ ] T-05.3 (CU-O74) Endpoints de reportes de auditoría y cumplimiento (exportación autorizada y auditada).
- [ ] T-05.4 Permisos: solo Auditor/Compliance + aislamiento multi-tenant.

## Etapa 6 — Frontend (FASE 8)
- [ ] T-06.1 `AuditoriaPage`: dashboard + línea de tiempo + tabla paginada + filtros avanzados.
- [ ] T-06.2 Detalle del evento + comparación antes/después + historial (registro/usuario/sesión).
- [ ] T-06.3 Duración de sesiones + alertas + estado de integridad + exportación autorizada.
- [ ] T-06.4 Gráficos legibles y proporcionados (sin miniaturas deformadas).

## Etapa 7 — Pruebas (FASE 10)
- [ ] T-PRUEBAS.1 INSERT/UPDATE/DELETE registran evento correcto.
- [ ] T-PRUEBAS.2 Valores anterior/nuevo + usuario/rol + sesión + duración.
- [ ] T-PRUEBAS.3 Acceso denegado, exportación de logs, generación de alertas.
- [ ] T-PRUEBAS.4 Integridad por hash + detección de manipulación + cadena de custodia.
- [ ] T-PRUEBAS.5 Aislamiento por tenant + enmascaramiento de datos sensibles.
- [ ] T-PRUEBAS.6 Rendimiento con gran volumen + paginación/filtros + recuperación ante fallo del servicio de auditoría.

## Trazabilidad tareas ↔ casos de uso
| Etapa/Tarea | CU |
|---|---|
| T-01.* | CU-O61, CU-O62, CU-O11 |
| T-02.1 | CU-O63 | 
| T-02.2 | CU-O64 |
| T-02.3 | CU-O65 |
| T-02.4 | CU-O67 |
| T-02.5 | CU-O66, CU-O15 |
| T-03.1 | CU-O68, CU-O13 |
| T-03.2 | CU-O69 |
| T-03.3 | CU-O70 |
| T-03.4 | CU-O71 |
| T-03.5 | CU-O72 |
| T-04.1 | CU-O75 |
| T-04.2 | CU-O76 |
| T-04.3 | CU-O14 |
| T-05.* | CU-O73, CU-O74, CU-O12 |
| T-06.* | CU-O73 (UI), FASE 8 |
