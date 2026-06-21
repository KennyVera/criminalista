# Plan — Nivel Operativo

> Plan de elaboración/entrega de especificaciones operativas (no de código). Organizado por paquete.

## Objetivo del Plan

Dejar especificados y trazables los 76 casos de uso operativos (CU-O01…CU-O60 + **CU-O61…CU-O76 del
NIVEL AUDITORÍA**) agrupados en los 12 paquetes UML, listos para una futura planificación de
implementación. La ampliación de P03 tiene su propio plan por etapas en
`003-operativo/P03-auditoria/plan.md`.

## Secuencia Recomendada (por dependencias)

| Orden | Paquete | OP | Justificación | Estado |
|---|---|---|---|---|
| 1 | P01 Autenticación y Seguridad | OP1 | Habilita todo acceso | Especificado |
| 2 | P02 Administración del Sistema | OP2 | Provisión de instituciones/usuarios | Especificado |
| 3 | P03 Auditoría y Trazabilidad | OP3 | Base legal y de cumplimiento | Especificado |
| 3.1 | **P03 ampliación — NIVEL AUDITORÍA (CU-O61…O76)** | OP3 | Auditoría total y centralizada, transversal a P01–P12; ver `P03-auditoria/` | Especificado (pend. aprobación PC-A1…A6) |
| 4 | P05 Gestión de Expedientes | OP5 | Núcleo del producto | Especificado |
| 5 | P07 Gestión de Involucrados | OP7 | Datos vinculados a expedientes | Especificado |
| 6 | P06 Gestión de Evidencias | OP6 | Custodia ligada a expedientes | Especificado |
| 7 | P04 Dashboard y Analítica | OP4 | Consume datos operativos | Especificado |
| 8 | P08 Reportería y Exportación | OP8 | Consume datos y analítica | Especificado |
| 9 | P09 Comercial B2G | OP9 | Cara de negocio (OE1) | Especificado |
| 10 | P10 Ecosistema de APIs | OP10 | Cara de negocio (OE2) | Especificado |
| 11 | P11 Cloud y SLA | OP11 | Cara de negocio (OE3) | Especificado |
| 12 | P12 Gobierno de Datos e BI | OP12 | Consolida todo (OE4) | Especificado |

## Dependencias Clave

- P01/P02/P03 son prerrequisito transversal.
- P04, P08 y P12 dependen de la existencia de datos (P05–P07, P09–P11).

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Custodia mal modelada | Invalidez legal | Reforzar RS-07/RN-02 y criterios de aceptación |
| Predicción sin datos suficientes | Resultados poco fiables | PC-O2; marcar dependencia de datos |
| Gráficos ilegibles | Incumple RI-04 | Estándares de visualización en `005`/`004` |
| Auditoría sobre Parquet (no append-only) | Pérdida de inmutabilidad | Decisión PC-A1 (PostgreSQL append-only o MinIO WORM) + hash encadenado; ver `P03-auditoria/spec.md` |
| Cobertura de auditoría incompleta (sin ORM) | Eventos no registrados | Middleware + decorador de servicios obligatorio (CU-O61) |

## Métricas de Éxito

KPI-20..24 (producto), KPI-13/14 (analítica), KPI-21/22 (custodia), KPI-18/19 (auditoría).

## Próximos Pasos

Tras aprobación, ejecutar `/speckit-plan` por paquete operativo para planificar la implementación.
