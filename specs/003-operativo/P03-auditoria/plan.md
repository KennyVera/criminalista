# Plan de Implementación — P03 Auditoría y Trazabilidad (AMPLIACIÓN)

> **CASOS DE USO NUEVOS — NIVEL AUDITORÍA.** Plan por etapas. **No se implementa hasta aprobar la
> especificación (`spec.md`) y resolver los pendientes PC-A1…PC-A6.** Ninguna etapa elimina
> funcionalidades actuales.

## Enfoque general
Captura **transversal** vía middleware + decorador de servicios (no triggers, porque los datos de
negocio viven en MinIO/Parquet sin ORM). Escritura **append-only** con `previous_hash`, asíncrona
con Celery y buffer de respaldo. Consulta y reportes restringidos a Auditor/Compliance.

## Etapas

### Etapa 0 — Aprobación y decisiones (sin código)
- Validar `spec.md`. Resolver PC-A1 (almacenamiento) y PC-A2…PC-A6.
- Confirmar lista de eventos (FASE 4) y de alertas (FASE 5).

### Etapa 1 — Núcleo de auditoría (CU-O61, CU-O62 ampliado)
- `AuditService.record()` + cálculo de `event_hash`/`previous_hash` + enmascaramiento.
- Modelo de datos `audit_events` + `audit_event_changes` + `audit_sessions` (según PC-A1).
- `AuditMiddleware`: contexto request (IP, UA→navegador/SO/dispositivo, endpoint, método, código,
  duración, correlation/trace, sesión).
- Decorador `@audited` para CRUD en servicios. Extensión de `AuthService` para ciclo de sesión.

### Etapa 2 — Cobertura por dominio
- CU-O63 roles/permisos/privilegios y accesos denegados.
- CU-O64 acceso a información sensible (helpers `audit_access`).
- CU-O65 expedientes, CU-O67 involucrados.
- CU-O66 evidencias + **hash de evidencia** + `audit_custody_events` (habilita CU-O15).

### Etapa 3 — Exportaciones, administración, APIs, cloud, BI
- CU-O68 reportes/exportaciones (`audit_exports`, marca de agua, motivo).
- CU-O69 administración/configuración (catálogos, parámetros, multi-tenant, licencias).
- CU-O70 APIs/integraciones (`audit_api_events`, **sin secretos**).
- CU-O71 cloud/continuidad (backups/restore/DR/SLA). CU-O72 analítica/BI/IA.

### Etapa 4 — Integridad, retención, alertas
- CU-O75 verificación de integridad (job Celery beat) + `audit_integrity_checks`.
- CU-O76 retención y archivado (`audit_retention_policies`, `audit_archives`).
- Motor de alertas (FASE 5) → `audit_security_alerts` (amplía CU-O14).

### Etapa 5 — API de consulta y reportes (CU-O73, CU-O74)
- Implementar `auditoria_trazabilidad/views.py` + `urls.py` (hoy vacío).
- Endpoints: tablero, detalle, línea de tiempo, exportación autorizada, reportes de cumplimiento.
- Permisos: solo Auditor/Compliance; aislamiento multi-tenant.

### Etapa 6 — Frontend (FASE 8)
- `AuditoriaPage`: dashboard, línea de tiempo, tabla paginada, filtros avanzados, detalle
  antes/después, historial por registro/usuario/sesión, duración de sesiones, alertas, estado de
  integridad, exportación autorizada, gráficos legibles (sin miniaturas deformadas).

### Etapa 7 — Pruebas y validación (FASE 10/11)
- Suite de pruebas (ver `tasks.md` T-PRUEBAS) y verificación de los 15 criterios de aceptación.

## Arquitectura de captura (resumen)
```
Request ─▶ AuditMiddleware (contextvar: ip, ua, endpoint, sesión, correlation_id)
                 │
   Servicios ────┼─▶ @audited(accion, entidad)  ─▶ AuditService.record(evento)
   (CRUD)        │                                     │ enmascara → hash(previous_hash)
   Lecturas ─────┴─▶ audit_access(entidad,id,modo)     │ append-only (async Celery + buffer)
                                                        ▼
                                          audit_events (+ tablas satélite)
                                                        │
                          Celery beat ─▶ verificación de integridad (CU-O75) ─▶ alertas
```

## Entregables al finalizar (cada etapa)
Archivos modificados · migraciones/tablas creadas · endpoints creados · componentes frontend ·
pruebas realizadas · CU implementados · pendientes · instrucciones para ejecutar y verificar.
