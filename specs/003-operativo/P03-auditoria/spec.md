# Especificación — P03 Auditoría y Trazabilidad (AMPLIACIÓN)

> **CASOS DE USO NUEVOS — NIVEL AUDITORÍA.** Amplía el paquete **P03** sin eliminar ni cambiar los
> casos existentes (CU-O11…CU-O15), que se **conservan, completan y amplían**. Agrega CU-O61…CU-O76
> marcados como **"Implementado adicional"**. Subordinada a la constitución y a `000-sistema-general/`.
> **Fase de especificación: NO se implementa código hasta aprobación.**

| Metadato | Valor |
|---|---|
| Paquete | P03 — Auditoría y Trazabilidad |
| OP / OT / OE | OP3 / OT5 / habilitador OE1–OE4 |
| Nivel | Operativo (transversal a todo el sistema) |
| Departamento | D06 Seguridad & Cumplimiento |
| Actor principal | A05 Auditor / Oficial de Cumplimiento |
| Versión spec | 1.0.0 (borrador) |
| Estado | Especificado — pendiente de aprobación |

---

## 1. FASE 1 — Diagnóstico de la Auditoría Actual

### 1.1 Stack tecnológico
- **Django 5.1.15 + DRF 3.17.1.** Autenticación: **JWT HS256 manual** (PyJWT), password con **bcrypt**.
- **Persistencia NO relacional:** los datos de negocio y de auditoría se guardan como **Parquet en
  MinIO (S3)** vía `pandas`+`boto3`. **SQLite** solo guarda metadatos internos de Django.
  **PocketBase** sirve el dataset crudo; **DuckDB** consulta analítica sobre Parquet.
- **Redis + Celery** disponibles (cache, broker, tareas programadas).
- `psycopg2-binary` está presente pero **PostgreSQL no se usa en runtime** hoy.

> **Implicación crítica:** no existe ORM de Django para datos de negocio; por tanto **no se pueden
> usar signals ni triggers de base de datos** para capturar auditoría sobre las tablas de negocio.
> La captura debe hacerse en **middleware + capa de servicios**.

### 1.2 Qué auditoría existe hoy
- **Tabla `app_audit_logs`** (Parquet en MinIO). Campos actuales:
  `id_log, fk_usuario, accion, tabla_afectada, detalle, direccion_ip, fecha_hora`.
  Se escribe por llamada **manual** (`_audit()`), no automática.
- **Tabla `app_sesiones_activas`** (sesiones): `id_sesion, fk_usuario, token_jti, email,
  nombre_rol, numero_placa, nombres, apellidos, direccion_ip, user_agent, fecha_inicio,
  fecha_ultimo_acceso, fecha_expiracion, activa, fecha_cierre, motivo_cierre`.
- **Tabla `app_expediente_bitacora`** (bitácora de avance de investigación, distinta de seguridad).
- **Paquete `auditoria_trazabilidad`**: existe la carpeta pero **vacía**, sin `views.py`/`urls.py`
  ni endpoint → **hoy no hay forma de consultar la auditoría desde la UI**.

### 1.3 Eventos que SÍ se registran hoy
`LOGIN, LOGIN_FAILED, LOGOUT, ACCOUNT_LOCKED, SESSION_CLOSED_BY_ADMIN, PASSWORD_RESET_REQUEST,
PASSWORD_RESET_OK, ASIGNAR_DETECTIVE, REMOVER_DETECTIVE, SEED_AUTH, BACKUP_RESTORE, BACKUP_FAILED`.

### 1.4 Vacíos detectados (NO se auditan hoy)
- CRUD de **usuarios**, cambios de **permisos por rol**, CRUD de **catálogos/zonas/políticas/parámetros**.
- **Expedientes** (creación/estado/cierre), **evidencias** (subida/consulta/descarga), **involucrados**.
- **Generación/exportación** de informes PDF, exportación de datos, consultas a dashboards.
- **Accesos denegados** (no se registran de forma centralizada).

### 1.5 Carencias de integridad y seguridad
- ❌ **No es append-only:** `append_row` reescribe el Parquet completo → un registro previo podría
  alterarse. ❌ **Sin hash de integridad** ni encadenamiento. ❌ **IDs por `max()+1`** (riesgo en
  concurrencia). ❌ **Evidencias sin hash** ni cadena de custodia real (solo string fijo
  `"En custodia"`). ❌ **RBAC nominal:** los permisos finos (`sys_rol_permisos`) existen pero **no
  se aplican**; la autorización es por **nombre de rol**. ❌ **Mono-institución** (sin tenant).

### 1.6 Conclusión del diagnóstico
La base existe (logs de auth, sesiones con IP/UA) pero es **insuficiente para auditoría total**:
cobertura parcial, sin inmutabilidad, sin integridad criptográfica, sin UI de consulta y sin
cadena de custodia. La ampliación debe resolver estos cinco frentes.

---

## 2. FASE 2 — Casos de Uso (existentes ampliados + nuevos)

### 2.1 Existentes (se conservan y completan — NO cambian de código)
| CU | Estado | Ampliación |
|---|---|---|
| CU-O11 Registrar bitácora de acceso | Conservado/ampliado | Pasa a evento centralizado con contexto completo (sesión, IP, dispositivo, hash). |
| CU-O12 Consultar trazabilidad de actividad | Conservado/ampliado | Alimenta el tablero central (CU-O73) con filtros avanzados. |
| CU-O13 Exportar logs de auditoría | Conservado/ampliado | Exportación autorizada y auditada (CU-O74). |
| CU-O14 Generar alerta de manipulación | Conservado/ampliado | Integrado al motor de alertas (FASE 5) y verificación de integridad (CU-O75). |
| CU-O15 Validar cadena de custodia | Conservado/ampliado | Se apoya en CU-O66 (auditoría de evidencias) y hash de evidencia. |

### 2.2 Nuevos — NIVEL AUDITORÍA (CU-O61…CU-O76, "Implementado adicional")
El detalle completo (objetivo, actores, precondiciones, entradas, flujos, excepciones, salidas,
reglas, RF, RNF, criterios Dado/Cuando/Entonces, dependencias, fuera de alcance) está en
`specs/004-uml-documentacion/casos-uso.md`, sección **"CASOS DE USO NUEVOS — NIVEL AUDITORÍA (P03)"**.

| CU | Nombre |
|---|---|
| CU-O61 | Registrar operaciones CRUD del sistema |
| CU-O62 | Auditar autenticación y sesiones |
| CU-O63 | Auditar roles, permisos y privilegios |
| CU-O64 | Auditar acceso a información sensible |
| CU-O65 | Auditar expedientes criminales |
| CU-O66 | Auditar evidencias y cadena de custodia |
| CU-O67 | Auditar involucrados |
| CU-O68 | Auditar reportes, archivos y exportaciones |
| CU-O69 | Auditar administración y configuración |
| CU-O70 | Auditar APIs e integraciones |
| CU-O71 | Auditar infraestructura cloud y continuidad |
| CU-O72 | Auditar analítica, BI e inteligencia artificial |
| CU-O73 | Consultar tablero central de auditoría |
| CU-O74 | Generar reportes de auditoría y cumplimiento |
| CU-O75 | Verificar integridad de la auditoría |
| CU-O76 | Gestionar retención y archivado de auditoría |

---

## 3. FASE 5 — Arquitectura Propuesta

> Diseñada para el stack real (MinIO/Parquet, sin ORM). Captura en middleware + servicios, no en triggers.

### 3.1 Componentes
1. **`AuditMiddleware` (DRF):** intercepta cada request/response. Captura contexto:
   `request_id`, `correlation_id`, `trace_id`, IP, User-Agent (→ navegador/SO/dispositivo parseado),
   endpoint, método HTTP, código de respuesta, duración, usuario/sesión (desde el JWT), ambiente.
   Publica el contexto en un `contextvar` request-scoped.
2. **`AuditService.record(evento)`:** punto único de escritura. Normaliza, **enmascara datos
   sensibles**, calcula `event_hash` y enlaza `previous_hash` (cadena), y persiste **append-only**.
3. **Decorador `@audited(accion, entidad, tipo_operacion)`:** envuelve operaciones de escritura en
   la capa de servicios (create/update/delete/asignar/vincular…), capturando `valor_anterior` y
   `valor_nuevo` + diff.
4. **Helpers de acceso sensible:** `audit_access(entidad, id, modo)` para SELECT/visualización/
   descarga/exportación de información reservada (CU-O64).
5. **Escritura asíncrona con Celery** + *buffer* local de respaldo: si el servicio de auditoría
   falla, el evento no se pierde (cola de reintento) y se genera alerta (FASE 5).
6. **Job de integridad (Celery beat):** verificación periódica de la cadena de hashes (CU-O75).
7. **API de consulta (`auditoria_trazabilidad/views.py`):** endpoints de tablero, detalle,
   exportación y reportes (CU-O73/O74), **solo para Auditor/Compliance**.
8. **Frontend `AuditoriaPage`:** dashboard, línea de tiempo, tabla paginada, filtros, detalle
   antes/después, integridad y exportación (FASE 8).

### 3.2 Decisión de almacenamiento (Pendiente por confirmar — PC-A1)
Dos opciones; se recomienda la **Opción A**:

- **Opción A (recomendada): PostgreSQL append-only dedicado para auditoría.**
  Tablas append-only con `REVOKE UPDATE, DELETE` a roles de app + **trigger `BEFORE UPDATE/DELETE`
  que lanza excepción**, `previous_hash` para encadenar, sellado de tiempo en servidor (UTC).
  Da inmutabilidad real, integridad y consultas eficientes con índices/particionado por fecha.
  Los datos de negocio siguen en MinIO; solo la auditoría usa PostgreSQL.
- **Opción B (consistente con stack actual): MinIO/Parquet particionado + WORM.**
  Escritura particionada por fecha (`audit/yyyy/mm/dd/…`), nunca reescribe particiones cerradas,
  `previous_hash` para encadenar, y verificación de integridad por job. Menos garantías ACID; exige
  buffer y control de concurrencia cuidadoso.

### 3.3 Mecanismo de captura por capa (ya que no hay ORM)
| Capa | Qué captura | Cómo |
|---|---|---|
| Middleware | Sesión, IP, UA, endpoint, método, código, duración, correlation/trace | `AuditMiddleware` + contextvar |
| Servicios | CRUD, valores antes/después, motivo, resultado | Decorador `@audited` |
| Lecturas sensibles | Consulta/visualización/descarga/exportación | `audit_access(...)` explícito |
| Auth/Sesiones | login/logout/MFA/bloqueos/duración | Extensión de `AuthService._audit` |
| APIs | request, código, latencia, scopes (sin secretos) | Middleware + capa API |
| Cloud/Backups | backup/restore/incidentes/DR | Hooks en servicios cloud/Celery |

---

## 4. FASE 7 — Modelo de Datos de Auditoría

Tabla central **`audit_events`** relacionada con tablas satélite. Claves foráneas lógicas por
`id_evento`. Para registros que pueden eliminarse en negocio, se guarda **copia histórica** del
valor en `audit_event_changes` (no se pierde la evidencia).

| Tabla | Propósito | Campos clave |
|---|---|---|
| `audit_events` | Evento central de auditoría | `id_evento (UUID), ts_utc, ts_local, id_institucion, nombre_institucion, id_usuario, usuario, nombres, cargo, rol, departamento, id_sesion, modulo, paquete_uml, caso_uso, endpoint, metodo_http, accion, tipo_operacion, entidad, tabla_afectada, id_registro, resultado, codigo_respuesta, mensaje_error, duracion_ms, severidad, nivel_riesgo, evento_seguridad, origen, ambiente, request_id, correlation_id, trace_id, event_hash, previous_hash` |
| `audit_event_changes` | Valores antes/después por campo | `id_cambio, id_evento(FK), campo, valor_anterior(enmascarado), valor_nuevo(enmascarado), diff, motivo` |
| `audit_sessions` | Ciclo de vida de sesión | `id_sesion, id_usuario, inicio, ultima_actividad, cierre, duracion, metodo_auth, estado_mfa, ip, user_agent, navegador, so, tipo_dispositivo, canal, motivo_cierre, sesiones_simultaneas` |
| `audit_access_events` | Acceso a información sensible | `id_acceso, id_evento(FK), entidad, id_registro, modo_acceso(consulta/visualizacion/descarga/impresion/exportacion/modificacion/eliminacion/comparticion), clasificacion` |
| `audit_security_alerts` | Alertas de seguridad | `id_alerta, tipo, severidad, id_usuario, id_institucion, ts, evidencias(refs id_evento), estado, responsable, accion_tomada, fecha_cierre` |
| `audit_exports` | Exportaciones de datos/reportes/logs | `id_export, id_evento(FK), tipo, formato, parametros, rango_fechas, destinatarios, tamano, marca_agua, motivo` |
| `audit_api_events` | Llamadas a APIs/webhooks | `id_api_evento, id_evento(FK), api_key_ref(parcial), scopes, institucion, endpoint, metodo, codigo, latencia_ms, ip, sistema_externo, bytes, webhook_status, reintentos` |
| `audit_evidence_events` | Eventos de evidencia | `id_ev, id_evento(FK), id_evidencia, nombre_archivo, tamano, mime, hash_inicial, hash_recalculo, resultado_verificacion` |
| `audit_custody_events` | Cadena de custodia | `id_cust, id_evidencia, custodio_anterior, custodio_nuevo, ts_transferencia, motivo, ubicacion, ruptura(bool)` |
| `audit_integrity_checks` | Verificaciones de integridad | `id_check, ts, rango, resultado, rupturas_detectadas, firma/sello_tiempo` |
| `audit_retention_policies` | Políticas de retención por institución | `id_politica, id_institucion, entidad, dias_retencion, retencion_legal(bool), suspension_por_investigacion(bool)` |
| `audit_archives` | Archivado de históricos | `id_archivo, rango, ubicacion, autorizado_por, ts_archivado, ts_restauracion, restaurado_por` |

> **Nunca** se almacenan contraseñas, tokens completos, claves privadas ni API keys completas. En
> `valor_anterior`/`valor_nuevo` los campos sensibles van **enmascarados** (p. ej. `****1234`).

---

## 5. Requisitos Funcionales (P03 ampliado)

| ID | Requisito |
|---|---|
| RF-O-P03-01 | Registrar todo evento sensible (FASE 4) en `audit_events` con los datos obligatorios (FASE 3). |
| RF-O-P03-02 | Capturar valores anterior y nuevo (con diff) en operaciones de modificación. |
| RF-O-P03-03 | Conservar evidencia histórica ante eliminaciones (copia en `audit_event_changes`). |
| RF-O-P03-04 | Registrar ciclo de vida de sesión (inicio, última actividad, cierre, duración, dispositivo). |
| RF-O-P03-05 | Registrar accesos denegados y autorizaciones (rol/permiso efectivo). |
| RF-O-P03-06 | Auditar acceso a información sensible distinguiendo el modo (consulta/descarga/exportación…). |
| RF-O-P03-07 | Calcular hash por evento y encadenar con `previous_hash`. |
| RF-O-P03-08 | Detectar manipulación y generar alertas (FASE 5). |
| RF-O-P03-09 | Proveer tablero central con filtros avanzados (CU-O73). |
| RF-O-P03-10 | Generar reportes de auditoría y cumplimiento (CU-O74). |
| RF-O-P03-11 | Verificar integridad periódicamente (CU-O75). |
| RF-O-P03-12 | Gestionar retención y archivado (CU-O76). |
| RF-O-P03-13 | Auditar evidencias y cadena de custodia con hash (CU-O66) — habilita CU-O15. |
| RF-O-P03-14 | Auditar APIs/integraciones sin almacenar secretos (CU-O70). |

## 6. Requisitos No Funcionales (P03 ampliado)

| ID | Requisito |
|---|---|
| RNF-O-P03-01 | **Inmutabilidad:** logs append-only; ni usuarios funcionales ni administradores pueden alterar el historial. |
| RNF-O-P03-02 | **Integridad:** hash por evento + encadenamiento; verificación periódica. |
| RNF-O-P03-03 | **Confidencialidad:** solo Auditor/Compliance consulta auditoría completa; respeta multi-tenant. |
| RNF-O-P03-04 | **Tiempo en servidor, UTC** (+ hora local derivada). |
| RNF-O-P03-05 | **No bloquear** la operación principal: escritura asíncrona con buffer/reintento. |
| RNF-O-P03-06 | **Rendimiento:** soporta gran volumen; particionado por fecha e índices/paginación. |
| RNF-O-P03-07 | **Enmascaramiento** de datos sensibles; sin secretos en errores. |
| RNF-O-P03-08 | **Resiliencia:** si el servicio de auditoría falla, se encola y se alerta; no se pierden eventos. |
| RNF-O-P03-09 | **Legibilidad:** gráficos del tablero claros y proporcionados (RI-04, sin miniaturas). |

## 7. Reglas de Negocio y Seguridad (FASE 6)

Se adoptan íntegras las 20 reglas de la FASE 6 del requerimiento (append-only, no modificación por
ningún rol, solo Auditor/Compliance consulta, aislamiento multi-tenant, tiempo en servidor UTC,
hash + previous_hash, exportaciones auditadas, archivado sin perder integridad, no almacenar
secretos, enmascaramiento, retención configurable por institución, conservación legal de eventos
críticos y trazabilidad de toda alerta/revisión). Ver también `000-sistema-general/rules.md`
(RS-05, RS-06, RS-07, RN-02, RN-05).

## 8. Criterios de Aceptación Generales (FASE 11)

Se adoptan los 15 criterios de la FASE 11. Resumen verificable:
toda operación sensible genera evento (1); identifica usuario/rol/institución (2); identifica el
registro afectado (3); muestra antes/después (4); conserva evidencia ante borrado (5); registra
ciclo de sesión y duración (6); registra accesos denegados (7) y exportaciones (8); eventos
inmutables (9) y manipulación detectable (10); aislamiento multi-tenant (11); enmascaramiento (12);
reconstrucción completa por el auditor (13); filtros por usuario/rol/sesión/módulo/CU/entidad/
fecha/IP (14); interfaz clara y legible (15).

## 9. Dependencias

- P01 (identidad/sesión/JWT) y P02 (usuarios/roles, futuro tenant).
- Redis/Celery (escritura asíncrona y verificación periódica).
- Decisión de almacenamiento (PC-A1) y, si Opción A, disponibilidad de PostgreSQL.
- P06 (evidencias) para hash y custodia (CU-O66 ↔ CU-O15).

## 10. Fuera de Alcance

- Implementación de código (esta fase es solo especificación).
- Implementar RBAC fino completo (se documenta como dependencia/PC; se audita el "rol efectivo").
- Construir multi-tenant (se deja el campo `id_institucion` previsto; su implementación es de P02).
- SIEM externo / exportación a terceros (se deja como extensión futura).

## 11. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Parquet no es append-only | Pérdida de inmutabilidad | Opción A (PostgreSQL append-only) o WORM particionado (Opción B) |
| Sin ORM → no signals/triggers | Cobertura incompleta | Middleware + decorador de servicios obligatorio en cada escritura |
| Volumen alto de eventos | Degradación | Escritura asíncrona, particionado, índices, retención/archivado |
| Datos sensibles en logs | Fuga de información | Enmascaramiento y lista de campos prohibidos |
| Concurrencia en hash-chain | Cadena inconsistente | Serialización de escritura (cola única) y secuencia por partición |
| RBAC nominal actual | Auditar "permiso" impreciso | Registrar rol efectivo; alinear con mejora futura de permisos |

## 12. Pendientes por Confirmar

- **PC-A1:** Almacenamiento de auditoría — ¿PostgreSQL append-only (recomendado) o MinIO WORM?
- **PC-A2:** ¿Se introducirá multi-tenant ahora o solo se deja el campo `id_institucion` previsto?
- **PC-A3:** Política de retención por defecto y conservación legal de eventos críticos.
- **PC-A4:** Algoritmo de hash (SHA-256/512) y si se usa sellado de tiempo/firma.
- **PC-A5:** Parser de User-Agent (navegador/SO/dispositivo) a utilizar.
- **PC-A6:** Cobertura del RBAC fino (¿se activa `sys_rol_permisos` o se mantiene por rol?).
