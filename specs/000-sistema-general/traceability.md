# Matriz de Trazabilidad Maestra — CrimeTrack Analytics Corp

> Trazabilidad consolidada a nivel de objetivos y paquetes. El detalle por cada caso de uso
> está en `004-uml-documentacion/matriz-trazabilidad.md`. Ningún elemento queda huérfano.

## 1. Cadena Estratégica (OE → OT → OP → Paquete → Departamento → KPI)

| OE | Objetivo Estratégico | OT | Objetivo Táctico | OP | Objetivo Operativo | Paquete | Departamento | KPI principal |
|---|---|---|---|---|---|---|---|---|
| OE1 | Penetración de Mercado Digital y Adquisición Automatizada (Growth Hacking B2G) | OT1 | Automatizar adquisición y pipeline institucional | OP9 | Operar captación comercial B2G | P09 | D02 | KPI-01 CAC, KPI-02 Conversión de leads, KPI-03 Nº instituciones |
| OE2 | Escalabilidad Comercial vía Ecosistemas, Marketplaces y APIs | OT2 | Operar ecosistema de APIs, integraciones y marketplace | OP10 | Operar ecosistema de APIs | P10 | D03 | KPI-04 Nº APIs publicadas, KPI-05 Integraciones activas, KPI-06 Ingreso marketplace |
| OE3 | Expansión Continua en Cloud de Alta Disponibilidad | OT3 | Garantizar disponibilidad, escalabilidad y continuidad | OP11 | Operar infraestructura cloud y SLA | P11 | D04 | KPI-07 Uptime %, KPI-08 Cumplimiento SLA %, KPI-09 RTO/RPO |
| OE4 | Inteligencia de Negocio Centralizada para Ventaja Competitiva | OT4 | Centralizar datos e inteligencia (BI) | OP12 | Consolidar datos e inteligencia corporativa | P12 | D05 | KPI-10 ARR/MRR, KPI-11 Precisión forecast, KPI-12 Cobertura DWH |
| OE4 | (analítica del producto alimenta BI) | OT4 | Centralizar datos e inteligencia (BI) | OP4 | Proveer analítica criminal accionable | P04 | D07/D05 | KPI-13 Uso de tableros, KPI-14 Cobertura analítica |
| OE1–OE4 (habilitador) | Seguridad y cumplimiento sostienen toda la oferta | OT5 | Gobierno, seguridad y cumplimiento | OP1 | Garantizar acceso seguro y autenticado | P01 | D06 | KPI-15 % accesos con MFA, KPI-16 Incidentes de seguridad |
| OE1–OE4 (habilitador) | Administración multi-institución | OT5 | Gobierno, seguridad y cumplimiento | OP2 | Administrar el sistema multi-institución | P02 | D01/D06 | KPI-17 Tiempo de aprovisionamiento |
| OE1–OE4 (habilitador) | Auditoría y trazabilidad como base legal | OT5 | Gobierno, seguridad y cumplimiento | OP3 | Auditar y trazar toda actividad | P03 | D06 | KPI-18 % eventos auditados, KPI-19 Integridad de logs |
| OE1, OE2, OE4 (producto vendible) | Excelencia criminalística | OT6 | Excelencia del producto criminalístico | OP5 | Gestionar ciclo de vida de expedientes | P05 | D07 | KPI-20 Tiempo de creación de expediente |
| OE1, OE2, OE4 | Excelencia criminalística | OT6 | Excelencia del producto criminalístico | OP6 | Custodiar evidencias con integridad | P06 | D07/D06 | KPI-21 % evidencias con hash válido, KPI-22 % cadena custodia íntegra |
| OE1, OE2, OE4 | Excelencia criminalística | OT6 | Excelencia del producto criminalístico | OP7 | Gestionar involucrados | P07 | D07 | KPI-23 % involucrados vinculados |
| OE1, OE2, OE4 | Excelencia criminalística | OT6 | Excelencia del producto criminalístico | OP8 | Generar reportería e informes | P08 | D07 | KPI-24 Tiempo de generación de reporte |

## 2. Cobertura de Casos de Uso por Nivel y Paquete

| Nivel | Casos de uso | Rango | Paquetes implicados |
|---|---|---|---|
| Estratégico | 10 | CU-E01…CU-E10 | P04, P09, P10, P11, P12 |
| Táctico | 16 | CU-T01…CU-T16 | P01, P02, P03, P09, P10, P11, P12 |
| Operativo | 60 | CU-O01…CU-O60 | P01–P12 |
| Operativo — NIVEL AUDITORÍA (nuevos) | 16 | CU-O61…CU-O76 | P03 (transversal a P01–P12) |

## 3. Casos de Uso Estratégicos → Trazabilidad

| CU | Nombre | OE | OT | Paquete | Actor | Depto | KPI | Resultado esperado |
|---|---|---|---|---|---|---|---|---|
| CU-E01 | Consultar Balanced Scorecard empresarial | OE4 | OT4 | P12 | A07 | D01 | KPI-10 | Cuadro de mando con 4 perspectivas actualizado |
| CU-E02 | Analizar penetración de mercado B2G | OE1 | OT1 | P12/P09 | A07,A08 | D01/D02 | KPI-03 | Tablero de penetración por región/segmento |
| CU-E03 | Analizar rentabilidad ARR/MRR gubernamental | OE4 | OT4 | P12 | A07 | D01 | KPI-10 | Reporte de ingresos recurrentes |
| CU-E04 | Definir metas y OKR corporativos | OE4 | OT4 | P12 | A07 | D01 | KPI-10..12 | OKR registrados y vinculados a KPIs |
| CU-E05 | Analizar ventaja competitiva global | OE4 | OT4 | P12 | A07,A11 | D05 | KPI-11 | Benchmark competitivo |
| CU-E06 | Evaluar disponibilidad cloud y SLA | OE3 | OT3 | P11 | A07,A10 | D04 | KPI-07,08 | Estado de SLA y uptime |
| CU-E07 | Revisar crecimiento por marketplace y APIs | OE2 | OT2 | P10/P09 | A07,A08 | D03/D02 | KPI-04,05,06 | Tablero de crecimiento de ecosistema |
| CU-E08 | Generar reporte ejecutivo corporativo | OE4 | OT4 | P08/P12 | A07 | D01 | KPI-10 | Informe ejecutivo consolidado |
| CU-E09 | Analizar expansión geográfica institucional | OE1 | OT1 | P12/P09 | A07,A08 | D01/D02 | KPI-03 | Mapa de expansión por jurisdicción |
| CU-E10 | Aprobar roadmap estratégico del producto | OE4 | OT4 | P12 | A07 | D01 | KPI-10..12 | Roadmap aprobado y versionado |

## 4. Casos de Uso Tácticos → Trazabilidad

| CU | Nombre | OE | OT | Paquete | Actor | Depto |
|---|---|---|---|---|---|---|
| CU-T01 | Gestionar campañas Growth Hacking B2G | OE1 | OT1 | P09 | A09 | D02 |
| CU-T02 | Administrar pipeline institucional | OE1 | OT1 | P09 | A08 | D02 |
| CU-T03 | Gestionar demos y pruebas piloto | OE1 | OT1 | P09 | A08 | D02 |
| CU-T04 | Gestionar licitaciones y RFP | OE1 | OT1 | P09 | A08, A15 | D02/D09 |
| CU-T05 | Configurar catálogo de APIs | OE2 | OT2 | P10 | A10 | D03 |
| CU-T06 | Gestionar integraciones con sistemas externos | OE2 | OT2 | P10 | A10,A14 | D03 |
| CU-T07 | Gestionar marketplace y planes SaaS | OE2 | OT2 | P10 | A08 | D02/D03 |
| CU-T08 | Configurar roles y permisos institucionales | OE1–OE4 | OT5 | P02/P01 | A01 | D06 |
| CU-T09 | Gestionar SLA y monitoreo cloud | OE3 | OT3 | P11 | A10 | D04 |
| CU-T10 | Gestionar data warehouse corporativo | OE4 | OT4 | P12 | A11 | D05 |
| CU-T11 | Configurar indicadores KPI y tableros | OE4 | OT4 | P12/P04 | A11 | D05 |
| CU-T12 | Gestionar auditoría y cumplimiento | OE1–OE4 | OT5 | P03 | A05 | D06 |
| CU-T13 | Gestionar paquetes de producto por cliente | OE1/OE2 | OT1/OT2 | P09 | A08 | D02 |
| CU-T14 | Administrar contratos y licencias B2G | OE1 | OT1 | P09/P02 | A08 | D09 |
| CU-T15 | Gestionar onboarding y capacitación institucional | OE1 | OT1 | P09 | A12 | D08 |
| CU-T16 | Gestionar soporte postventa y success | OE1 | OT1 | P09 | A12 | D08 |

## 5. Casos de Uso Operativos → Paquete / OP / Actor (resumen)

| Rango | Paquete | OP | Actor principal | Depto |
|---|---|---|---|---|
| CU-O01…O05 | P01 Autenticación y Seguridad | OP1 | A06/A01 | D06 |
| CU-O06…O10 | P02 Administración del Sistema | OP2 | A01 | D01/D06 |
| CU-O11…O15 | P03 Auditoría y Trazabilidad | OP3 | A05 | D06 |
| CU-O61…O76 (NIVEL AUDITORÍA, nuevos) | P03 Auditoría y Trazabilidad (ampliación transversal) | OP3 | A05/Sistema | D06 |
| CU-O16…O20 | P04 Dashboard y Analítica Criminal | OP4 | A03 | D07 |
| CU-O21…O25 | P05 Gestión de Expedientes | OP5 | A02 | D07 |
| CU-O26…O30 | P06 Gestión de Evidencias Digitales | OP6 | A04 | D07/D06 |
| CU-O31…O35 | P07 Gestión de Involucrados | OP7 | A02 | D07 |
| CU-O36…O40 | P08 Reportería y Exportación | OP8 | A02/A06 | D07 |
| CU-O41…O45 | P09 Gestión Comercial B2G | OP9 | A08 | D02 |
| CU-O46…O50 | P10 Ecosistema de APIs | OP10 | A10/A14 | D03 |
| CU-O51…O55 | P11 Gestión Cloud y SLA | OP11 | A10 | D04 |
| CU-O56…O60 | P12 Gobierno de Datos e BI | OP12 | A11 | D05 |

> El detalle fila-por-fila de los 76 CU operativos —incluidos los **16 nuevos de auditoría**
> CU-O61…CU-O76 (sección D)— con HU, RF, criterio de aceptación y resultado esperado está en
> `004-uml-documentacion/matriz-trazabilidad.md`. La especificación ampliada de P03 está en
> `003-operativo/P03-auditoria/`.

## 6. Catálogo de KPIs

| KPI | Nombre | OE | Fórmula/medida (referencial) |
|---|---|---|---|
| KPI-01 | CAC | OE1 | Gasto de adquisición / nº instituciones nuevas |
| KPI-02 | Conversión de leads B2G | OE1 | Leads ganados / leads totales |
| KPI-03 | Nº instituciones adquiridas | OE1 | Conteo por periodo |
| KPI-04 | Nº APIs publicadas | OE2 | Conteo de APIs activas en catálogo |
| KPI-05 | Integraciones activas | OE2 | Conteo de conectores/webhooks activos |
| KPI-06 | Ingreso por marketplace | OE2 | Suma de ingresos por planes/APIs |
| KPI-07 | Uptime % | OE3 | Tiempo disponible / tiempo total |
| KPI-08 | Cumplimiento SLA % | OE3 | SLA cumplidos / SLA comprometidos |
| KPI-09 | RTO/RPO | OE3 | Tiempo/punto de recuperación medidos |
| KPI-10 | ARR/MRR | OE4 | Ingreso recurrente anual/mensual |
| KPI-11 | Precisión de forecast | OE4 | 1 − error de pronóstico |
| KPI-12 | Cobertura de DWH | OE4 | % fuentes integradas al data warehouse |
| KPI-13 | Uso de tableros | OE4 | Sesiones/usuarios activos en dashboards |
| KPI-14 | Cobertura analítica | OE4 | % expedientes con analítica aplicada |
| KPI-15 | % accesos con MFA | habilitador | Accesos con MFA / accesos críticos |
| KPI-16 | Incidentes de seguridad | habilitador | Conteo por periodo (objetivo: ↓) |
| KPI-17 | Tiempo de aprovisionamiento | habilitador | Tiempo de alta de institución |
| KPI-18 | % eventos auditados | habilitador | Eventos auditados / eventos relevantes |
| KPI-19 | Integridad de logs | habilitador | % logs verificados sin alteración |
| KPI-20 | Tiempo de creación de expediente | producto | Promedio por expediente |
| KPI-21 | % evidencias con hash válido | producto | Evidencias con hash verificado / total |
| KPI-22 | % cadena de custodia íntegra | producto | Custodias sin ruptura / total |
| KPI-23 | % involucrados vinculados | producto | Involucrados con expediente / total |
| KPI-24 | Tiempo de generación de reporte | producto | Promedio por reporte |

## Pendientes por Confirmar

- **PC-T1:** Metas numéricas objetivo de cada KPI por trimestre.
- **PC-T2:** Validar el actor **A15 Abogado/Especialista Legal & Contratos** (estado "Implementado adicional"), usado en CU-T04/CU-T14.
