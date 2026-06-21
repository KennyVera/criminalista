# Especificación — Nivel Operativo

> Nivel empresarial **Operativo**. Casos de uso CU-O01…CU-O60, organizados por paquete UML
> (P01–P12), **más los 16 casos de uso nuevos de auditoría CU-O61…CU-O76** (NIVEL AUDITORÍA, P03,
> "Implementado adicional") **y los 2 casos nuevos de operaciones de patrulla CU-O77…CU-O78**
> (P05, "Implementado adicional"). Subordinada a la constitución y a `000-sistema-general/`. **Sin
> implementación de código.** El detalle completo de cada caso de uso (actor, objetivo, precondición,
> flujo principal, flujo alternativo y criterio de aceptación) está en
> `004-uml-documentacion/casos-uso.md`. La **ampliación de P03** (diagnóstico, arquitectura, modelo
> de datos, plan, tareas, riesgos y pendientes) está en `003-operativo/P03-auditoria/`.

## 1. Objetivo

Especificar la operación diaria del sistema: tanto el **producto criminalístico** que opera el
cliente (autenticación, expedientes, evidencias, involucrados, analítica, reportería, auditoría)
como la **operación de negocio** (captación comercial, APIs, cloud/SLA, BI). Cada caso de uso es
trazable a un objetivo operativo (OP) → táctico (OT) → estratégico (OE).

## 2. Contexto

Es el nivel donde se ejecuta, verifica y demuestra la funcionalidad. Alimenta de datos al nivel
táctico (configuración) y estratégico (indicadores). Cubre las dos caras del sistema (producto y
negocio) sin alterar el enfoque B2G.

## 3. Actores

A01 Administrador, A02 Investigador, A03 Analista Criminal, A04 Custodio de Evidencia, A05 Auditor,
A06 Usuario Institucional, A08 Gerente Comercial, A10 SRE, A11 Analista BI, A14 Sistema Externo.

## 4. Departamento Responsable

D07 Operaciones Criminalísticas (producto), D02 Comercial, D03 Plataforma, D04 Cloud, D05 BI,
D06 Seguridad & Cumplimiento.

## 5. Nivel Empresarial

Operativo.

## 6. Paquete UML Relacionado (mapa CU-O ↔ Paquete ↔ OP)

| Paquete | OP | Casos de uso operativos |
|---|---|---|
| P01 Autenticación y Seguridad | OP1 | CU-O01, CU-O02, CU-O03, CU-O04, CU-O05 |
| P02 Administración del Sistema | OP2 | CU-O06, CU-O07, CU-O08, CU-O09, CU-O10 |
| P03 Auditoría y Trazabilidad | OP3 | CU-O11, CU-O12, CU-O13, CU-O14, CU-O15; **CU-O61…CU-O76 (NIVEL AUDITORÍA, nuevos)** |
| P04 Dashboard y Analítica Criminal | OP4 | CU-O16, CU-O17, CU-O18, CU-O19, CU-O20 |
| P05 Gestión de Expedientes | OP5 | CU-O21, CU-O22, CU-O23, CU-O24, CU-O25; **CU-O77, CU-O78 (operaciones de patrulla, nuevos)** |
| P06 Gestión de Evidencias Digitales | OP6 | CU-O26, CU-O27, CU-O28, CU-O29, CU-O30 |
| P07 Gestión de Involucrados | OP7 | CU-O31, CU-O32, CU-O33, CU-O34, CU-O35 |
| P08 Reportería y Exportación | OP8 | CU-O36, CU-O37, CU-O38, CU-O39, CU-O40 |
| P09 Gestión Comercial B2G | OP9 | CU-O41, CU-O42, CU-O43, CU-O44, CU-O45 |
| P10 Ecosistema de APIs | OP10 | CU-O46, CU-O47, CU-O48, CU-O49, CU-O50 |
| P11 Gestión Cloud y SLA | OP11 | CU-O51, CU-O52, CU-O53, CU-O54, CU-O55 |
| P12 Gobierno de Datos e BI | OP12 | CU-O56, CU-O57, CU-O58, CU-O59, CU-O60 |

## 7. Objetivos Relacionados

| OP | Objetivo Operativo | OT | OE |
|---|---|---|---|
| OP1 | Garantizar acceso seguro y autenticado | OT5 | OE1–OE4 (habilitador) |
| OP2 | Administrar el sistema multi-institución | OT5 | OE1–OE4 (habilitador) |
| OP3 | Auditar y trazar toda actividad | OT5 | OE1–OE4 (habilitador) |
| OP4 | Proveer analítica criminal accionable | OT4 | OE4 |
| OP5 | Gestionar ciclo de vida de expedientes | OT6 | OE1/OE2/OE4 (producto) |
| OP6 | Custodiar evidencias con integridad | OT6 | OE1/OE2/OE4 (producto) |
| OP7 | Gestionar involucrados | OT6 | OE1/OE2/OE4 (producto) |
| OP8 | Generar reportería e informes | OT6 | OE1/OE2/OE4 (producto) |
| OP9 | Operar captación comercial B2G | OT1 | OE1 |
| OP10 | Operar ecosistema de APIs | OT2 | OE2 |
| OP11 | Operar infraestructura cloud y SLA | OT3 | OE3 |
| OP12 | Consolidar datos e inteligencia corporativa | OT4 | OE4 |

## 8. Requisitos Funcionales (por paquete)

| ID | Requisito | Paquete |
|---|---|---|
| RF-O-P01 | Autenticación, MFA, recuperación, sesiones y validación de permisos. | P01 |
| RF-O-P02 | Alta de instituciones, usuarios/roles, parámetros, licencias y contratos/SLA. | P02 |
| RF-O-P03 | Bitácora de acceso, consulta de trazabilidad, exportación de logs, alertas y cadena de custodia. | P03 |
| RF-O-P03-01…14 | **Auditoría total y centralizada (NIVEL AUDITORÍA):** registro append-only de toda operación (CRUD, auth/sesiones, RBAC, acceso sensible, expedientes, evidencias/custodia, involucrados, exportaciones, configuración, APIs, cloud, BI), valores antes/después, hash encadenado, accesos denegados, alertas, verificación de integridad, retención/archivado, tablero y reportes de cumplimiento. Detalle en `P03-auditoria/spec.md`. | P03 |
| RF-O-P04 | Mapa de calor, indicadores, filtros analíticos, tendencias y predicción criminal. | P04 |
| RF-O-P05 | Crear, asignar, actualizar, vincular y cerrar expedientes. | P05 |
| RF-O-P06 | Registrar, cargar, hashear, custodiar y consultar evidencias. | P06 |
| RF-O-P07 | Registrar víctima/sospechoso/testigo, vincular y consultar historial. | P07 |
| RF-O-P08 | Generar, exportar (PDF/Excel), programar, emitir y enviar reportes. | P08 |
| RF-O-P09 | Registrar lead, calificar oportunidad, programar demo, registrar RFP, generar propuesta. | P09 |
| RF-O-P10 | Registrar API key, consultar documentación, configurar webhook, registrar consumo, gestionar conector. | P10 |
| RF-O-P11 | Monitorear uptime, ejecutar backup, escalamiento automático, registrar incidente SLA, ejecutar DR. | P11 |
| RF-O-P12 | Consolidar datos, calcular KPI, generar benchmark, exportar tablero, ejecutar forecast. | P12 |

## 9. Requisitos No Funcionales

| ID | Requisito |
|---|---|
| RNF-O-01 | Operaciones interactivas < 2 s; reportes pesados de forma asíncrona. |
| RNF-O-02 | Toda operación sobre datos delictivos es auditada y atribuible (RS-05/06). |
| RNF-O-03 | Integridad criptográfica de evidencias (hash) y cadena de custodia (RS-07). |
| RNF-O-04 | Aislamiento por tenant (RN-06). |
| RNF-O-05 | Gráficos (mapa de calor, tendencias) legibles y proporcionados (RI-04). |
| RNF-O-06 | **Auditoría inmutable (append-only) con hash encadenado**; ningún rol altera el historial; tiempo en servidor/UTC; enmascaramiento de datos sensibles; sin secretos en logs (P03 ampliado). |
| RNF-O-07 | **Auditoría no bloqueante** (escritura asíncrona con buffer/reintento) y resiliente ante fallos del servicio de auditoría. |

## 10. Reglas de Negocio

RN-01, RN-02 (custodia), RN-05 (auditoría), RN-06 (tenant), RN-08 (exportación), RN-09 (cierre de expediente).

## 11. Entradas

Credenciales; datos de instituciones/usuarios; expedientes, evidencias e involucrados; filtros
analíticos; datos comerciales; llamadas a APIs; métricas de infraestructura; fuentes para BI.

## 12. Salidas

Sesiones válidas; expedientes y registros con custodia; evidencias con hash; visualizaciones
analíticas; reportes PDF/Excel; respuestas de API/webhooks; alertas; KPIs/benchmarks/forecasts;
logs de auditoría.

## 13. Precondiciones

Usuario autenticado y autorizado; institución activa; configuración táctica aplicada (roles, SLA,
KPIs); servicios cloud disponibles.

## 14. Flujo Principal

1. El usuario operativo se autentica (MFA si aplica) y el sistema valida permisos.
2. Ejecuta la operación del paquete correspondiente (P01–P12).
3. El sistema valida reglas (tenant, contrato, custodia) y persiste con auditoría.
4. Genera salidas (registro, visualización, reporte, respuesta de API) y, si aplica, alertas.
5. Los datos alimentan la analítica (P04) y la inteligencia de negocio (P12).

## 15. Flujos Alternativos

- **FA-O1:** permiso insuficiente → operación denegada y auditada (CU-O05).
- **FA-O2:** evidencia con hash inconsistente → alerta de manipulación (CU-O14, CU-O28).
- **FA-O3:** operación vía API → mismas reglas que la UI (CU-O46…CU-O50).

## 16. Excepciones

- **EX-O1:** indisponibilidad cloud → continuidad/DR (CU-O55).
- **EX-O2:** intento de cierre de expediente incompleto → bloqueado (RN-09).
- **EX-O3:** ruptura de cadena de custodia → alerta y preservación del historial (RN-02).

## 17. Criterios de Aceptación (Dado / Cuando / Entonces) — representativos del nivel

- **CA-O-01** — Dado un usuario con credenciales válidas, Cuando inicia sesión con MFA, Entonces
  obtiene una sesión válida y queda registrado en la bitácora (CU-O01, CU-O11).
- **CA-O-21** — Dado un investigador autorizado, Cuando crea un expediente, Entonces se genera con
  folio único, estado inicial y registro de auditoría (CU-O21).
- **CA-O-26** — Dada una evidencia digital, Cuando se registra y se carga su archivo, Entonces el
  sistema calcula su hash e inicia su cadena de custodia (CU-O26, CU-O27, CU-O28).
- **CA-O-37** — Dado un reporte operativo, Cuando se exporta a PDF/Excel, Entonces el documento es
  legible, completo y la exportación queda auditada (CU-O37).
> El criterio de aceptación específico de cada uno de los 60 CU está en `004-uml-documentacion/casos-uso.md`.

## 18. Dependencias

P01/P02/P03 habilitan a todos; P04–P08 dependen de datos operativos; P09–P12 dependen de
configuración táctica (002) e infraestructura cloud.

## 19. Fuera de Alcance

Configuración táctica (002) y decisiones estratégicas (001); implementación de código. Modificación
de OE1–OE4 o del alcance B2G.

## 20. Historias de Usuario Relacionadas

HU-O-01…HU-O-60 (una por caso de uso) y **HU-O-61…HU-O-76 (NIVEL AUDITORÍA, nuevas)** en
`004-uml-documentacion/historias-usuario.md`.

## Pendientes por Confirmar

- **PC-O1:** Algoritmo de hash de evidencia y formato de almacenamiento (ligado a PC-R2).
- **PC-O2:** Modelo y fuente de datos para la predicción criminal (CU-O20) y el forecast B2G (CU-O60).
- **PC-O3:** Política de retención de logs y backups (CU-O13, CU-O52).
- **PC-O4 (auditoría):** Decisiones PC-A1…PC-A6 de la ampliación P03 (almacenamiento append-only,
  multi-tenant, retención, algoritmo de hash, parser de User-Agent, alcance del RBAC fino). Ver
  `003-operativo/P03-auditoria/spec.md`.
