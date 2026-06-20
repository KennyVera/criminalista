# Reglas del Sistema — CrimeTrack Analytics Corp

> Reglas de negocio, seguridad, arquitectura, documentación, implementación y validación
> aplicables a todo el proyecto. Subordinadas a `.specify/memory/constitution.md`.

## 1. Reglas de Negocio (RN)

| ID | Regla |
|---|---|
| RN-01 | Ninguna funcionalidad existe sin trazabilidad hasta al menos un OE (OE1–OE4). |
| RN-02 | La cadena de custodia de evidencias es inviolable: toda alteración se registra y nunca sobrescribe el historial. |
| RN-03 | El alcance empresarial B2G es inmutable; no se reduce a "uso policial interno" ni se amplía fuera de seguridad/justicia sin enmienda. |
| RN-04 | Los cuatro objetivos estratégicos OE1–OE4 son inmutables. |
| RN-05 | Todo evento relevante sobre datos sensibles genera auditoría inmutable y atribuible. |
| RN-06 | Cada institución cliente opera con aislamiento de datos (multi-tenant). |
| RN-07 | Las capacidades disponibles para un cliente dependen de su contrato/licencia vigente. |
| RN-08 | Toda exportación de datos requiere autorización por rol y queda auditada. |
| RN-09 | Un expediente solo puede cerrarse si cumple sus criterios de completitud y custodia. |
| RN-10 | Las APIs expuestas son versionadas, documentadas y sujetas a las mismas reglas de seguridad que la UI. |

## 2. Reglas de Seguridad (RS)

| ID | Regla |
|---|---|
| RS-01 Autenticación | Acceso solo con identidad autenticada; credenciales con hashing fuerte; tokens/sesiones firmados con clave de longitud segura (≥ 32 bytes). |
| RS-02 Roles y permisos | RBAC con privilegio mínimo; permisos verificados en backend; cada acción sensible exige permiso explícito. |
| RS-03 Sesiones | Expiración, renovación controlada y revocación; estado de sesión consultable y revocable por administración. |
| RS-04 MFA | MFA obligatorio para roles administrativos y operaciones de alto impacto (gestión de usuarios, exportaciones masivas, configuración, restauración de respaldos) y cuando el cliente lo exija. |
| RS-05 Auditoría | Registro inmutable de login/logout, accesos, cambios de datos, exportaciones y cambios de configuración/permisos, con usuario, fecha/hora, origen y resultado. |
| RS-06 Trazabilidad | Toda operación sobre datos delictivos es atribuible y reconstruible desde los registros. |
| RS-07 Cadena de custodia | Evidencias con historial íntegro de creación, acceso, modificación, transferencia y custodia; validez legal preservada. |
| RS-08 Cifrado | Cifrado en tránsito (TLS) y en reposo para datos sensibles. |
| RS-09 Detección | Alertas ante intentos de manipulación o accesos anómalos. |

## 3. Reglas de Arquitectura (RA)

| ID | Regla |
|---|---|
| RA-01 | Modularidad por paquetes UML (P01–P12) con contratos explícitos y bajo acoplamiento. |
| RA-02 | Separación por niveles empresariales (estratégico/táctico/operativo). |
| RA-03 | Trazabilidad de requisitos preservada en la estructura (requisito↔componente↔CU). |
| RA-04 | Integración mediante APIs versionadas, documentadas y seguras (OE2). |
| RA-05 | Despliegue en cloud de alta disponibilidad con redundancia y DR (OE3). |
| RA-06 | Gobierno de datos: clasificación, calidad, retención, privacidad y soberanía; aislamiento por tenant. |
| RA-07 | Capa de analítica criminal que alimenta la inteligencia de negocio (OE4) sin comprometer privacidad ni custodia. |

## 4. Reglas de Documentación (RD)

| ID | Regla |
|---|---|
| RD-01 | Todo caso de uso incluye: actor, objetivo, precondición, flujo principal, flujo alternativo y criterio de aceptación. |
| RD-02 | Toda historia de usuario se asocia a un caso de uso y a un objetivo operativo. |
| RD-03 | No debe existir funcionalidad sin relación con objetivos estratégicos, tácticos u operativos. |
| RD-04 | Cada módulo se documenta antes de implementarse. |
| RD-05 | La documentación es clara y legible; los diagramas son proporcionados y legibles. |
| RD-06 | Información faltante se registra en una sección "Pendientes por confirmar". |

## 5. Reglas de Implementación (RI) — (no se ejecuta código en esta fase)

| ID | Regla |
|---|---|
| RI-01 | No se programan funcionalidades que no estén especificadas. |
| RI-02 | No se modifica el alcance empresarial B2G. |
| RI-03 | No se cambian los cuatro objetivos estratégicos obligatorios. |
| RI-04 | No se crean gráficos miniatura, alargados o ilegibles. |
| RI-05 | Cada módulo se documenta antes de implementarse. |
| RI-06 | Cambios de alcance: primero se actualiza la especificación; luego se implementa. |

## 6. Reglas de Validación (RV)

| ID | Regla |
|---|---|
| RV-01 | Cada módulo debe tener checklist verificable. |
| RV-02 | Cada requisito debe ser verificable. |
| RV-03 | Cada caso de uso debe tener criterios de aceptación. |
| RV-04 | Cada funcionalidad implementada debe poder mostrarse en video con su caso de uso documentado. |
| RV-05 | "Hecho" = checklist cumplido + criterios satisfechos + trazabilidad + demostrable. |

## 7. Reglas de Gestión de Cambios y Duplicados (RC)

| ID | Regla |
|---|---|
| RC-01 | Si un caso de uso parece duplicado, no se elimina; se propone reorganización (estado "Propuesta de reorganización"). |
| RC-02 | Si falta un paquete, caso de uso o historia, se agrega y se marca "Implementado adicional". |
| RC-03 | Toda enmienda a reglas requiere justificación, actualización de trazabilidad y versión. |

## Pendientes por Confirmar

- **PC-R1:** Política exacta de intentos fallidos de login y bloqueo de cuenta.
- **PC-R2:** Estándar criptográfico de hash de evidencia (p. ej., SHA-256/512) a fijar por cumplimiento.
- **PC-R3:** Matriz fina de permisos por rol institucional (a confirmar con clientes piloto).
