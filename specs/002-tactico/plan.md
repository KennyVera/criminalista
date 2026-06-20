# Plan — Nivel Táctico

> Plan de elaboración/entrega de especificaciones tácticas (no de código).

## Objetivo del Plan

Dejar especificadas y trazables las 16 capacidades tácticas (CU-T01…CU-T16) que conectan estrategia
(001) y operación (003).

## Fases

| Fase | Descripción | Paquetes | Estado |
|---|---|---|---|
| T-F1 | Especificar capacidades comerciales (campañas, pipeline, demos, RFP, paquetes, contratos, onboarding, soporte) | P09 | Especificado |
| T-F2 | Especificar ecosistema (catálogo APIs, integraciones, marketplace) | P10 | Especificado |
| T-F3 | Especificar SLA y monitoreo cloud | P11 | Especificado |
| T-F4 | Especificar DWH y KPIs/tableros | P12, P04 | Especificado |
| T-F5 | Especificar roles institucionales y auditoría/cumplimiento | P02, P01, P03 | Especificado |
| T-F6 | Trazabilidad y checklist | — | Especificado |
| T-F7 | Revisión y aprobación | — | Pendiente por confirmar |

## Dependencias

- Operativo (003) provee la ejecución; táctico la configura.
- Seguridad (P01) y auditoría (P03) deben estar especificadas.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| APIs sin estándar | Integraciones frágiles | Definir estándar (PC-T3) |
| Permisos mal definidos | Riesgo de seguridad | Doble control + MFA (RNF-T-02) |
| SLA inconsistente | Incumplimiento OE3 | Validación de umbrales (EX-T2) |

## Métricas de Éxito

KPI-02 Conversión, KPI-04/05/06 ecosistema, KPI-08 SLA, KPI-12 cobertura DWH.

## Próximos Pasos

Tras aprobación, planificar implementación por paquete (P09, P10, P11, P12) con `/speckit-plan`.
