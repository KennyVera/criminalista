# Matriz de Trazabilidad Detallada — CrimeTrack Analytics Corp

> Trazabilidad fila-por-fila de los 102 casos de uso (incluye los **16 nuevos de auditoría**
> CU-O61…CU-O76 del paquete P03, ver sección **D**). Relaciona: OE, Objetivo Estratégico, OT,
> Objetivo Táctico, OP, Objetivo Operativo, Caso de Uso, Historia de Usuario, Paquete UML, Actor,
> Departamento, Requisito Funcional, KPI, Funcionalidad/Módulo, Criterio de Aceptación y Resultado
> Esperado. Complementa la matriz maestra de `000-sistema-general/traceability.md`. Sin huérfanos.

## Leyenda de Objetivos

| Código | Descripción |
|---|---|
| OE1 | Penetración de Mercado Digital y Adquisición Automatizada (Growth Hacking B2G) |
| OE2 | Escalabilidad Comercial vía Ecosistemas, Marketplaces y APIs |
| OE3 | Expansión Continua en Cloud de Alta Disponibilidad |
| OE4 | Inteligencia de Negocio Centralizada para Ventaja Competitiva |
| OT1 | Adquisición y pipeline automatizado · OT2 Ecosistema de APIs/marketplace · OT3 Disponibilidad y continuidad |
| OT4 | Centralizar datos e inteligencia · OT5 Gobierno/seguridad/cumplimiento · OT6 Excelencia del producto |
| OP1..OP12 | Objetivos operativos (uno por paquete P01..P12) |

---

## A. Matriz Estratégica (CU-E)

| CU | HU | OE | OT | Paquete | Actor | Depto | RF | KPI | Funcionalidad/Módulo | Criterio | Resultado esperado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CU-E01 | HU-E-01 | OE4 | OT4 | P12 | A07 | D01 | RF-E-01 | KPI-10 | Balanced Scorecard | CA-E-01 | BSC con 4 perspectivas vigente |
| CU-E02 | HU-E-02 | OE1 | OT1 | P12/P09 | A07,A08 | D01/D02 | RF-E-02 | KPI-03 | Análisis de mercado | CA-E-01 | Penetración por región/segmento |
| CU-E03 | HU-E-03 | OE4 | OT4 | P12 | A07 | D01 | RF-E-03 | KPI-10 | ARR/MRR | CA-E-02 | Ingreso recurrente exportable |
| CU-E04 | HU-E-04 | OE4 | OT4 | P12 | A07 | D01 | RF-E-04 | KPI-10..12 | OKR corporativos | CA-E-03 | OKR ligados a KPIs y a OE |
| CU-E05 | HU-E-05 | OE4 | OT4 | P12 | A07,A11 | D05 | RF-E-05 | KPI-11 | Benchmark competitivo | CA-E-01 | Comparativa de ventaja |
| CU-E06 | HU-E-06 | OE3 | OT3 | P11 | A07,A10 | D04 | RF-E-06 | KPI-07/08 | Tablero SLA | CA-E-01 | Uptime y cumplimiento SLA |
| CU-E07 | HU-E-07 | OE2 | OT2 | P10/P09 | A07,A08 | D03/D02 | RF-E-07 | KPI-04/05/06 | Tablero ecosistema | CA-E-01 | Crecimiento de APIs/marketplace |
| CU-E08 | HU-E-08 | OE4 | OT4 | P08/P12 | A07 | D01 | RF-E-08 | KPI-10 | Reporte ejecutivo | CA-E-04 | Informe consolidado y legible |
| CU-E09 | HU-E-09 | OE1 | OT1 | P12/P09 | A07,A08 | D01/D02 | RF-E-09 | KPI-03 | Mapa de expansión | CA-E-01 | Cobertura/potencial por jurisdicción |
| CU-E10 | HU-E-10 | OE4 | OT4 | P12 | A07 | D01 | RF-E-10 | KPI-10..12 | Gobierno de roadmap | CA-E-04 | Roadmap aprobado y versionado |

---

## B. Matriz Táctica (CU-T)

| CU | HU | OE | OT | Paquete | Actor | Depto | RF | KPI | Funcionalidad/Módulo | Criterio | Resultado esperado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CU-T01 | HU-T-01 | OE1 | OT1 | P09 | A09 | D02 | RF-T-01 | KPI-02 | Campañas Growth B2G | CA-T-01 | Campaña medible |
| CU-T02 | HU-T-02 | OE1 | OT1 | P09 | A08 | D02 | RF-T-02 | KPI-02 | Pipeline institucional | CA-T-01 | Etapas actualizadas |
| CU-T03 | HU-T-03 | OE1 | OT1 | P09 | A08 | D02 | RF-T-03 | KPI-02 | Demos/pilotos | CA-T-01 | Piloto con resultados |
| CU-T04 | HU-T-04 | OE1 | OT1 | P09 | A08,A15 | D02/D09 | RF-T-04 | KPI-03 | Licitaciones/RFP | CA-T-01 | Historial de RFP |
| CU-T05 | HU-T-05 | OE2 | OT2 | P10 | A10 | D03 | RF-T-05 | KPI-04 | Catálogo de APIs | CA-T-04 | API versionada/documentada |
| CU-T06 | HU-T-06 | OE2 | OT2 | P10 | A10,A14 | D03 | RF-T-06 | KPI-05 | Integraciones | CA-T-04 | Conectividad validada |
| CU-T07 | HU-T-07 | OE2 | OT2 | P10 | A08 | D02/D03 | RF-T-07 | KPI-06 | Marketplace/planes | CA-T-04 | Plan publicado |
| CU-T08 | HU-T-08 | OE1–OE4 | OT5 | P02/P01 | A01 | D06 | RF-T-08 | KPI-15 | Roles institucionales | CA-T-02 | Privilegio mínimo auditado |
| CU-T09 | HU-T-09 | OE3 | OT3 | P11 | A10 | D04 | RF-T-09 | KPI-08 | SLA/monitoreo | CA-T-03 | Alertas por incumplimiento |
| CU-T10 | HU-T-10 | OE4 | OT4 | P12 | A11 | D05 | RF-T-10 | KPI-12 | Data warehouse | CA-T-04 | DWH con calidad/linaje |
| CU-T11 | HU-T-11 | OE4 | OT4 | P12/P04 | A11 | D05 | RF-T-11 | KPI-13 | KPIs/tableros | CA-T-04 | KPI en tablero legible |
| CU-T12 | HU-T-12 | OE1–OE4 | OT5 | P03 | A05 | D06 | RF-T-12 | KPI-18/19 | Auditoría/cumplimiento | CA-T-02 | Evidencia de cumplimiento |
| CU-T13 | HU-T-13 | OE1/OE2 | OT1/OT2 | P09 | A08 | D02 | RF-T-13 | KPI-06 | Paquetes por cliente | CA-T-01 | Capacidades según contrato |
| CU-T14 | HU-T-14 | OE1 | OT1 | P09/P02 | A08,A15 | D09 | RF-T-14 | KPI-10 | Contratos/licencias | CA-T-02 | Contrato vigente auditado |
| CU-T15 | HU-T-15 | OE1 | OT1 | P09 | A12 | D08 | RF-T-15 | KPI-03 | Onboarding | CA-T-01 | Cliente activo/capacitado |
| CU-T16 | HU-T-16 | OE1 | OT1 | P09 | A12 | D08 | RF-T-16 | KPI-02 | Soporte/success | CA-T-01 | Caso cerrado con satisfacción |

---

## C. Matriz Operativa (CU-O)

| CU | HU | OE | OT | OP | Paquete | Actor | Depto | RF | KPI | Módulo | Resultado esperado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CU-O01 | HU-O-01 | OE1–OE4 | OT5 | OP1 | P01 | A06 | D06 | RF-O-P01 | KPI-15 | Login | Sesión válida + bitácora |
| CU-O02 | HU-O-02 | OE1–OE4 | OT5 | OP1 | P01 | A06,A01 | D06 | RF-O-P01 | KPI-15 | MFA | Segundo factor validado |
| CU-O03 | HU-O-03 | OE1–OE4 | OT5 | OP1 | P01 | A06 | D06 | RF-O-P01 | KPI-16 | Recuperación | Contraseña restablecida |
| CU-O04 | HU-O-04 | OE1–OE4 | OT5 | OP1 | P01 | A01 | D06 | RF-O-P01 | KPI-16 | Sesiones | Sesión revocada/auditada |
| CU-O05 | HU-O-05 | OE1–OE4 | OT5 | OP1 | P01 | A06 | D06 | RF-O-P01 | KPI-16 | RBAC | Acción autorizada/denegada |
| CU-O06 | HU-O-06 | OE1 | OT1 | OP2 | P02 | A01 | D01 | RF-O-P02 | KPI-17 | Alta institución | Tenant activo aislado |
| CU-O07 | HU-O-07 | OE1–OE4 | OT5 | OP2 | P02 | A01 | D06 | RF-O-P02 | KPI-17 | Usuarios/roles | Rol asignado/auditado |
| CU-O08 | HU-O-08 | OE1–OE4 | OT5 | OP2 | P02 | A01 | D06 | RF-O-P02 | KPI-17 | Parámetros | Configuración aplicada |
| CU-O09 | HU-O-09 | OE1/OE2 | OT1 | OP2 | P02 | A01,A08 | D02 | RF-O-P02 | KPI-06 | Licencias | Capacidades habilitadas |
| CU-O10 | HU-O-10 | OE1/OE3 | OT1 | OP2 | P02 | A08,A15 | D09 | RF-O-P02 | KPI-10 | Contratos/SLA | Contrato vigente |
| CU-O11 | HU-O-11 | OE1–OE4 | OT5 | OP3 | P03 | Sistema | D06 | RF-O-P03 | KPI-18 | Bitácora | Registro inmutable |
| CU-O12 | HU-O-12 | OE1–OE4 | OT5 | OP3 | P03 | A05 | D06 | RF-O-P03 | KPI-18 | Trazabilidad | Traza reconstruible |
| CU-O13 | HU-O-13 | OE1–OE4 | OT5 | OP3 | P03 | A05 | D06 | RF-O-P03 | KPI-18 | Export logs | Exportación auditada |
| CU-O14 | HU-O-14 | OE1–OE4 | OT5 | OP3 | P03 | A05,Sistema | D06 | RF-O-P03 | KPI-19 | Alerta manipulación | Alerta + historial intacto |
| CU-O15 | HU-O-15 | OE1–OE4 | OT5 | OP3 | P03 | A05,A04 | D06 | RF-O-P03 | KPI-22 | Validar custodia | Integridad confirmada |
| CU-O16 | HU-O-16 | OE4 | OT4 | OP4 | P04 | A03 | D07 | RF-O-P04 | KPI-14 | Mapa de calor | Visualización legible |
| CU-O17 | HU-O-17 | OE4 | OT4 | OP4 | P04 | A03 | D07 | RF-O-P04 | KPI-13 | Indicadores | Valores correctos |
| CU-O18 | HU-O-18 | OE4 | OT4 | OP4 | P04 | A03 | D07 | RF-O-P04 | KPI-14 | Filtros | Resultado filtrado |
| CU-O19 | HU-O-19 | OE4 | OT4 | OP4 | P04 | A03 | D07 | RF-O-P04 | KPI-14 | Tendencias | Serie legible |
| CU-O20 | HU-O-20 | OE4 | OT4 | OP4 | P04 | A03 | D07 | RF-O-P04 | KPI-11 | Predicción | Estimación con confianza |
| CU-O21 | HU-O-21 | OE4 | OT6 | OP5 | P05 | A02 | D07 | RF-O-P05 | KPI-20 | Crear expediente | Folio único + auditoría |
| CU-O22 | HU-O-22 | OE4 | OT6 | OP5 | P05 | A01,A02 | D07 | RF-O-P05 | KPI-20 | Asignar | Responsable registrado |
| CU-O23 | HU-O-23 | OE4 | OT6 | OP5 | P05 | A02 | D07 | RF-O-P05 | KPI-20 | Estado | Transición válida |
| CU-O24 | HU-O-24 | OE4 | OT6 | OP5 | P05 | A02 | D07 | RF-O-P05 | KPI-23 | Vincular | Relaciones trazables |
| CU-O25 | HU-O-25 | OE4 | OT6 | OP5 | P05 | A02,A01 | D07 | RF-O-P05 | KPI-20 | Cerrar | Cierre solo si completo |
| CU-O26 | HU-O-26 | OE4 | OT6 | OP6 | P06 | A04 | D07 | RF-O-P06 | KPI-21 | Registrar evidencia | Metadatos + custodia |
| CU-O27 | HU-O-27 | OE4 | OT6 | OP6 | P06 | A04 | D07 | RF-O-P06 | KPI-21 | Cargar archivo | Almacenado cifrado |
| CU-O28 | HU-O-28 | OE4 | OT6 | OP6 | P06 | Sistema | D06 | RF-O-P06 | KPI-21 | Hash | Hash verificable |
| CU-O29 | HU-O-29 | OE4 | OT6 | OP6 | P06 | A04 | D07 | RF-O-P06 | KPI-22 | Custodia | Historial sin pérdida |
| CU-O30 | HU-O-30 | OE4 | OT6 | OP6 | P06 | A02,A05 | D07 | RF-O-P06 | KPI-22 | Consultar evidencia | Acceso autorizado auditado |
| CU-O31 | HU-O-31 | OE4 | OT6 | OP7 | P07 | A02 | D07 | RF-O-P07 | KPI-23 | Registrar víctima | Datos protegidos |
| CU-O32 | HU-O-32 | OE4 | OT6 | OP7 | P07 | A02 | D07 | RF-O-P07 | KPI-23 | Registrar sospechoso | Vinculable a caso |
| CU-O33 | HU-O-33 | OE4 | OT6 | OP7 | P07 | A02 | D07 | RF-O-P07 | KPI-23 | Registrar testigo | Nivel de protección |
| CU-O34 | HU-O-34 | OE4 | OT6 | OP7 | P07 | A02 | D07 | RF-O-P07 | KPI-23 | Vincular involucrado | Relación trazable |
| CU-O35 | HU-O-35 | OE4 | OT6 | OP7 | P07 | A02,A03 | D07 | RF-O-P07 | KPI-23 | Historial | Vínculos autorizados |
| CU-O36 | HU-O-36 | OE4 | OT6 | OP8 | P08 | A02,A06 | D07 | RF-O-P08 | KPI-24 | Generar reporte | Contenido correcto |
| CU-O37 | HU-O-37 | OE4 | OT6 | OP8 | P08 | A02,A06 | D07 | RF-O-P08 | KPI-24 | Exportar PDF/Excel | Archivo legible auditado |
| CU-O38 | HU-O-38 | OE4 | OT6 | OP8 | P08 | A01,A06 | D07 | RF-O-P08 | KPI-24 | Programar reporte | Entrega automática |
| CU-O39 | HU-O-39 | OE4 | OT6 | OP8 | P08 | A06 | D07 | RF-O-P08 | KPI-24 | Informe institucional | Formato oficial |
| CU-O40 | HU-O-40 | OE4 | OT6 | OP8 | P08 | A06 | D07 | RF-O-P08 | KPI-24 | Enviar reporte | Solo a autorizados |
| CU-O41 | HU-O-41 | OE1 | OT1 | OP9 | P09 | A09,A08 | D02 | RF-O-P09 | KPI-02 | Registrar lead | Lead para calificar |
| CU-O42 | HU-O-42 | OE1 | OT1 | OP9 | P09 | A08 | D02 | RF-O-P09 | KPI-02 | Calificar | Oportunidad en pipeline |
| CU-O43 | HU-O-43 | OE1 | OT1 | OP9 | P09 | A08 | D02 | RF-O-P09 | KPI-02 | Programar demo | Demo agendada |
| CU-O44 | HU-O-44 | OE1 | OT1 | OP9 | P09 | A08,A15 | D02/D09 | RF-O-P09 | KPI-03 | Avance RFP | Hito en historial |
| CU-O45 | HU-O-45 | OE1 | OT1 | OP9 | P09 | A08 | D02 | RF-O-P09 | KPI-01 | Propuesta B2G | Documento legible |
| CU-O46 | HU-O-46 | OE2 | OT2 | OP10 | P10 | A10,A14 | D03 | RF-O-P10 | KPI-04 | API key | Key con scopes |
| CU-O47 | HU-O-47 | OE2 | OT2 | OP10 | P10 | A14,A10 | D03 | RF-O-P10 | KPI-04 | Documentación API | Versionada/legible |
| CU-O48 | HU-O-48 | OE2 | OT2 | OP10 | P10 | A10,A14 | D03 | RF-O-P10 | KPI-05 | Webhook | Evento validado |
| CU-O49 | HU-O-49 | OE2 | OT2 | OP10 | P10 | Sistema | D03 | RF-O-P10 | KPI-05/06 | Consumo API | Uso contabilizado |
| CU-O50 | HU-O-50 | OE2 | OT2 | OP10 | P10 | A10 | D03 | RF-O-P10 | KPI-05 | Conector | Salud registrada |
| CU-O51 | HU-O-51 | OE3 | OT3 | OP11 | P11 | A10 | D04 | RF-O-P11 | KPI-07 | Uptime | Disponibilidad medida |
| CU-O52 | HU-O-52 | OE3 | OT3 | OP11 | P11 | A10,Sistema | D04 | RF-O-P11 | KPI-09 | Backup | Respaldo registrado |
| CU-O53 | HU-O-53 | OE3 | OT3 | OP11 | P11 | A10,Sistema | D04 | RF-O-P11 | KPI-07 | Autoescalado | Recursos escalados |
| CU-O54 | HU-O-54 | OE3 | OT3 | OP11 | P11 | A10 | D04 | RF-O-P11 | KPI-08 | Incidente SLA | Afecta cumplimiento |
| CU-O55 | HU-O-55 | OE3 | OT3 | OP11 | P11 | A10 | D04 | RF-O-P11 | KPI-09 | DR | Restauración en RTO/RPO |
| CU-O56 | HU-O-56 | OE4 | OT4 | OP12 | P12 | A11 | D05 | RF-O-P12 | KPI-12 | Consolidar datos | DWH íntegro |
| CU-O57 | HU-O-57 | OE4 | OT4 | OP12 | P12 | A11,Sistema | D05 | RF-O-P12 | KPI-13 | Calcular KPI | Valor correcto |
| CU-O58 | HU-O-58 | OE4 | OT4 | OP12 | P12 | A11 | D05 | RF-O-P12 | KPI-11 | Benchmark | Comparativa legible |
| CU-O59 | HU-O-59 | OE4 | OT4 | OP12 | P12 | A07,A11 | D05 | RF-O-P12 | KPI-13 | Exportar tablero | Export proporcionado |
| CU-O60 | HU-O-60 | OE4 | OT4 | OP12 | P12 | A11 | D05 | RF-O-P12 | KPI-11 | Forecast B2G | Proyección con precisión |

---

## D. Matriz Operativa — NIVEL AUDITORÍA (CU-O61…CU-O76, NUEVOS)

> **Implementado adicional.** Amplían P03 (OP3) sin alterar CU-O11…CU-O15. RF de detalle:
> RF-O-P03-01…RF-O-P03-14 (ver `003-operativo/P03-auditoria/spec.md`).

| CU | HU | OE | OT | OP | Paquete | Actor | Depto | RF | KPI | Módulo | Resultado esperado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CU-O61 | HU-O-61 | OE1–OE4 | OT5 | OP3 | P03 | Sistema,A05 | D06 | RF-O-P03-01/02/03 | KPI-18 | Auditoría CRUD | Evento inmutable con antes/después |
| CU-O62 | HU-O-62 | OE1–OE4 | OT5 | OP3 | P03 | Sistema,A05 | D06 | RF-O-P03-04/05 | KPI-18 | Auditoría auth/sesiones | Ciclo y duración de sesión |
| CU-O63 | HU-O-63 | OE1–OE4 | OT5 | OP3 | P03 | Sistema,A01 | D06 | RF-O-P03-05 | KPI-19 | Auditoría RBAC | Cambios y accesos denegados |
| CU-O64 | HU-O-64 | OE1–OE4 | OT5 | OP3 | P03 | Sistema,A05 | D06 | RF-O-P03-06 | KPI-18 | Acceso sensible | Modo de acceso registrado |
| CU-O65 | HU-O-65 | OE4 | OT6 | OP3 | P03 | Sistema,A02 | D06 | RF-O-P03-01/02 | KPI-20 | Auditoría expedientes | Historial reconstruible |
| CU-O66 | HU-O-66 | OE4 | OT6 | OP3 | P03 | Sistema,A04 | D06 | RF-O-P03-13 | KPI-22 | Auditoría evidencias/custodia | Cadena con hash verificable |
| CU-O67 | HU-O-67 | OE4 | OT6 | OP3 | P03 | Sistema,A02 | D06 | RF-O-P03-01/06 | KPI-23 | Auditoría involucrados | Cambios con antes/después |
| CU-O68 | HU-O-68 | OE4 | OT6 | OP3 | P03 | Sistema,A06 | D06 | RF-O-P03-01 | KPI-24 | Auditoría exportaciones | Exportación auditada |
| CU-O69 | HU-O-69 | OE1–OE4 | OT5 | OP3 | P03 | Sistema,A01 | D06 | RF-O-P03-01 | KPI-17 | Auditoría configuración | Cambios críticos trazados |
| CU-O70 | HU-O-70 | OE2 | OT2 | OP3 | P03 | Sistema,A10 | D06 | RF-O-P03-14 | KPI-05 | Auditoría APIs | Consumo sin secretos |
| CU-O71 | HU-O-71 | OE3 | OT3 | OP3 | P03 | Sistema,A10 | D06 | RF-O-P03-01 | KPI-09 | Auditoría cloud/continuidad | Backups/incidentes trazados |
| CU-O72 | HU-O-72 | OE4 | OT4 | OP3 | P03 | Sistema,A11 | D06 | RF-O-P03-01/06 | KPI-13 | Auditoría BI/IA | Modelos y datasets trazados |
| CU-O73 | HU-O-73 | OE1–OE4 | OT5 | OP3 | P03 | A05 | D06 | RF-O-P03-09 | KPI-18 | Tablero central auditoría | Traza filtrable y legible |
| CU-O74 | HU-O-74 | OE1–OE4 | OT5 | OP3 | P03 | A05 | D06 | RF-O-P03-10 | KPI-19 | Reportes de cumplimiento | Reporte auditado y legible |
| CU-O75 | HU-O-75 | OE1–OE4 | OT5 | OP3 | P03 | Sistema,A05 | D06 | RF-O-P03-07/08/11 | KPI-19 | Verificación integridad | Manipulación detectable |
| CU-O76 | HU-O-76 | OE1–OE4 | OT5 | OP3 | P03 | A05,A01 | D06 | RF-O-P03-12 | KPI-18 | Retención/archivado | Histórico íntegro y autorizado |

---

## Verificación de Cobertura (sin huérfanos)

| Comprobación | Resultado |
|---|---|
| Todo CU tiene HU asociada | ✔ 102/102 (incl. CU-O61…O76) |
| Todo CU traza a un OE | ✔ 102/102 |
| Todo CU pertenece a un paquete (P01–P12) | ✔ (CU-O61…O76 en P03) |
| Todo OE se materializa en CU/HU | ✔ OE1–OE4 cubiertos |
| Todo CU tiene criterio de aceptación | ✔ (ver `casos-uso.md`) |
| Criterio detallado Dado/Cuando/Entonces | ✔ en `casos-uso.md` |

## Pendientes por Confirmar

- **PC-M1:** Confirmar metas numéricas por KPI (enlaza con PC-T1).
- **PC-M2:** Validar actor A15 (Legal & Contratos) — estado "Implementado adicional".
- **PC-M3:** Confirmar decisiones de auditoría PC-A1…PC-A6 (almacenamiento, tenant, retención, hash,
  parser UA, RBAC fino) descritas en `003-operativo/P03-auditoria/spec.md`.

