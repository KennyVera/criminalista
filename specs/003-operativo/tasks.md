# Tareas — Nivel Operativo

> Tareas de documentación/especificación (no de código). Cada tarea corresponde a un caso de uso
> operativo y traza a su paquete, OP y OE. Detalle del CU en `004-uml-documentacion/casos-uso.md`.
> Incluye las tareas del **NIVEL AUDITORÍA** (CU-O61…CU-O76, T-O-A61…T-O-A76) en P03.

## P01 — Autenticación y Seguridad (OP1)

| ID | CU | Tarea | OE | Estado |
|---|---|---|---|---|
| T-O-01 | CU-O01 | Especificar Iniciar sesión | habilitador | Especificado |
| T-O-02 | CU-O02 | Especificar Gestionar MFA | habilitador | Especificado |
| T-O-03 | CU-O03 | Especificar Recuperar contraseña | habilitador | Especificado |
| T-O-04 | CU-O04 | Especificar Gestionar sesiones activas | habilitador | Especificado |
| T-O-05 | CU-O05 | Especificar Validar permisos por rol | habilitador | Especificado |

## P02 — Administración del Sistema (OP2)

| ID | CU | Tarea | OE | Estado |
|---|---|---|---|---|
| T-O-06 | CU-O06 | Especificar Registrar institución cliente | OE1 | Especificado |
| T-O-07 | CU-O07 | Especificar Gestionar usuarios y roles | habilitador | Especificado |
| T-O-08 | CU-O08 | Especificar Configurar parámetros y catálogos | habilitador | Especificado |
| T-O-09 | CU-O09 | Especificar Gestionar licencias y planes | OE1/OE2 | Especificado |
| T-O-10 | CU-O10 | Especificar Registrar contrato y SLA | OE1/OE3 | Especificado |

## P03 — Auditoría y Trazabilidad (OP3)

| ID | CU | Tarea | OE | Estado |
|---|---|---|---|---|
| T-O-11 | CU-O11 | Especificar Registrar bitácora de acceso | habilitador | Especificado |
| T-O-12 | CU-O12 | Especificar Consultar trazabilidad de actividad | habilitador | Especificado |
| T-O-13 | CU-O13 | Especificar Exportar logs de auditoría | habilitador | Especificado |
| T-O-14 | CU-O14 | Especificar Generar alerta de manipulación | habilitador | Especificado |
| T-O-15 | CU-O15 | Especificar Validar cadena de custodia | habilitador | Especificado |

### P03 — NIVEL AUDITORÍA (casos de uso nuevos, "Implementado adicional")

> Detalle y plan de implementación por etapas en `003-operativo/P03-auditoria/` (spec/plan/tasks/checklist).

| ID | CU | Tarea | OE | Estado |
|---|---|---|---|---|
| T-O-A61 | CU-O61 | Especificar Registrar operaciones CRUD del sistema | habilitador | Especificado |
| T-O-A62 | CU-O62 | Especificar Auditar autenticación y sesiones | habilitador | Especificado |
| T-O-A63 | CU-O63 | Especificar Auditar roles, permisos y privilegios | habilitador | Especificado |
| T-O-A64 | CU-O64 | Especificar Auditar acceso a información sensible | habilitador | Especificado |
| T-O-A65 | CU-O65 | Especificar Auditar expedientes criminales | OE4 | Especificado |
| T-O-A66 | CU-O66 | Especificar Auditar evidencias y cadena de custodia | OE4 | Especificado |
| T-O-A67 | CU-O67 | Especificar Auditar involucrados | OE4 | Especificado |
| T-O-A68 | CU-O68 | Especificar Auditar reportes, archivos y exportaciones | OE4 | Especificado |
| T-O-A69 | CU-O69 | Especificar Auditar administración y configuración | habilitador | Especificado |
| T-O-A70 | CU-O70 | Especificar Auditar APIs e integraciones | OE2 | Especificado |
| T-O-A71 | CU-O71 | Especificar Auditar infraestructura cloud y continuidad | OE3 | Especificado |
| T-O-A72 | CU-O72 | Especificar Auditar analítica, BI e IA | OE4 | Especificado |
| T-O-A73 | CU-O73 | Especificar Consultar tablero central de auditoría | habilitador | Especificado |
| T-O-A74 | CU-O74 | Especificar Generar reportes de auditoría y cumplimiento | habilitador | Especificado |
| T-O-A75 | CU-O75 | Especificar Verificar integridad de la auditoría | habilitador | Especificado |
| T-O-A76 | CU-O76 | Especificar Gestionar retención y archivado de auditoría | habilitador | Especificado |

## P04 — Dashboard y Analítica Criminal (OP4)

| ID | CU | Tarea | OE | Estado |
|---|---|---|---|---|
| T-O-16 | CU-O16 | Especificar Visualizar mapa de calor criminal | OE4 | Especificado |
| T-O-17 | CU-O17 | Especificar Consultar indicadores criminales | OE4 | Especificado |
| T-O-18 | CU-O18 | Especificar Ejecutar filtros analíticos | OE4 | Especificado |
| T-O-19 | CU-O19 | Especificar Consultar tendencias delictivas | OE4 | Especificado |
| T-O-20 | CU-O20 | Especificar Generar predicción criminal | OE4 | Especificado |

## P05 — Gestión de Expedientes (OP5)

| ID | CU | Tarea | OE | Estado |
|---|---|---|---|---|
| T-O-21 | CU-O21 | Especificar Crear expediente criminal | OE4 | Especificado |
| T-O-22 | CU-O22 | Especificar Asignar investigador a expediente | OE4 | Especificado |
| T-O-23 | CU-O23 | Especificar Actualizar estado del expediente | OE4 | Especificado |
| T-O-24 | CU-O24 | Especificar Vincular delitos, evidencias e involucrados | OE4 | Especificado |
| T-O-25 | CU-O25 | Especificar Cerrar expediente criminal | OE4 | Especificado |

## P06 — Gestión de Evidencias Digitales (OP6)

| ID | CU | Tarea | OE | Estado |
|---|---|---|---|---|
| T-O-26 | CU-O26 | Especificar Registrar evidencia digital | OE4 | Especificado |
| T-O-27 | CU-O27 | Especificar Cargar archivo de evidencia | OE4 | Especificado |
| T-O-28 | CU-O28 | Especificar Calcular hash de evidencia | OE4 | Especificado |
| T-O-29 | CU-O29 | Especificar Gestionar custodia de evidencia | OE4 | Especificado |
| T-O-30 | CU-O30 | Especificar Consultar evidencia autorizada | OE4 | Especificado |

## P07 — Gestión de Involucrados (OP7)

| ID | CU | Tarea | OE | Estado |
|---|---|---|---|---|
| T-O-31 | CU-O31 | Especificar Registrar víctima | OE4 | Especificado |
| T-O-32 | CU-O32 | Especificar Registrar sospechoso | OE4 | Especificado |
| T-O-33 | CU-O33 | Especificar Registrar testigo | OE4 | Especificado |
| T-O-34 | CU-O34 | Especificar Vincular involucrado a expediente | OE4 | Especificado |
| T-O-35 | CU-O35 | Especificar Consultar historial de involucrado | OE4 | Especificado |

## P08 — Reportería y Exportación (OP8)

| ID | CU | Tarea | OE | Estado |
|---|---|---|---|---|
| T-O-36 | CU-O36 | Especificar Generar reporte operativo | OE4 | Especificado |
| T-O-37 | CU-O37 | Especificar Exportar reporte PDF/Excel | OE4 | Especificado |
| T-O-38 | CU-O38 | Especificar Programar reporte automático | OE4 | Especificado |
| T-O-39 | CU-O39 | Especificar Emitir informe institucional | OE4 | Especificado |
| T-O-40 | CU-O40 | Especificar Enviar reporte autorizado | OE4 | Especificado |

## P09 — Gestión Comercial B2G (OP9)

| ID | CU | Tarea | OE | Estado |
|---|---|---|---|---|
| T-O-41 | CU-O41 | Especificar Registrar lead B2G | OE1 | Especificado |
| T-O-42 | CU-O42 | Especificar Calificar oportunidad institucional | OE1 | Especificado |
| T-O-43 | CU-O43 | Especificar Programar demo institucional | OE1 | Especificado |
| T-O-44 | CU-O44 | Especificar Registrar avance de licitación/RFP | OE1 | Especificado |
| T-O-45 | CU-O45 | Especificar Generar propuesta comercial B2G | OE1 | Especificado |

## P10 — Ecosistema de APIs (OP10)

| ID | CU | Tarea | OE | Estado |
|---|---|---|---|---|
| T-O-46 | CU-O46 | Especificar Registrar API key institucional | OE2 | Especificado |
| T-O-47 | CU-O47 | Especificar Consultar documentación API | OE2 | Especificado |
| T-O-48 | CU-O48 | Especificar Configurar webhook institucional | OE2 | Especificado |
| T-O-49 | CU-O49 | Especificar Registrar consumo API | OE2 | Especificado |
| T-O-50 | CU-O50 | Especificar Gestionar conector externo | OE2 | Especificado |

## P11 — Gestión Cloud y SLA (OP11)

| ID | CU | Tarea | OE | Estado |
|---|---|---|---|---|
| T-O-51 | CU-O51 | Especificar Monitorear uptime del servicio | OE3 | Especificado |
| T-O-52 | CU-O52 | Especificar Ejecutar backup programado | OE3 | Especificado |
| T-O-53 | CU-O53 | Especificar Activar escalamiento automático | OE3 | Especificado |
| T-O-54 | CU-O54 | Especificar Registrar incidente SLA | OE3 | Especificado |
| T-O-55 | CU-O55 | Especificar Ejecutar recuperación ante desastres | OE3 | Especificado |

## P12 — Gobierno de Datos e BI (OP12)

| ID | CU | Tarea | OE | Estado |
|---|---|---|---|---|
| T-O-56 | CU-O56 | Especificar Consolidar datos comerciales y de uso | OE4 | Especificado |
| T-O-57 | CU-O57 | Especificar Calcular KPI corporativo | OE4 | Especificado |
| T-O-58 | CU-O58 | Especificar Generar benchmark institucional | OE4 | Especificado |
| T-O-59 | CU-O59 | Especificar Exportar tablero ejecutivo | OE4 | Especificado |
| T-O-60 | CU-O60 | Especificar Ejecutar modelo forecast de demanda B2G | OE4 | Especificado |

## Tareas Transversales

| ID | Tarea | Estado |
|---|---|---|
| T-O-61 | Construir trazabilidad CU-O↔HU-O↔RF↔criterio | Especificado |
| T-O-62 | Completar checklist del nivel | Especificado |
| T-O-63 | Revisión y aprobación | Pendiente por confirmar |
