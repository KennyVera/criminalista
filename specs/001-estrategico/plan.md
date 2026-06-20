# Plan — Nivel Estratégico

> Plan de elaboración/entrega (no de implementación de código). Define cómo se construirán y
> validarán las especificaciones y artefactos del nivel estratégico.

## Objetivo del Plan

Dejar listas, trazables y validadas las capacidades estratégicas (CU-E01…CU-E10) para que, en una
fase posterior, puedan planificarse e implementarse sin ambigüedad.

## Enfoque

- Consumir la taxonomía de `000-sistema-general/` (OE/OT/OP, KPIs, actores, departamentos).
- Especificar cada capacidad estratégica como consumo de datos consolidados (P12/P04).
- Garantizar trazabilidad ascendente a OE1–OE4 y descendente a tácticos/operativos.

## Fases

| Fase | Descripción | Entregable | Estado |
|---|---|---|---|
| E-F1 | Validar taxonomía estratégica (OE↔OT↔KPI) | Tabla OE/OT/KPI | Especificado |
| E-F2 | Especificar CU-E01…CU-E10 (20 puntos) | `spec.md` | Especificado |
| E-F3 | Definir tableros (BSC, mercado, ARR/MRR, SLA, ecosistema) | Catálogo de tableros | Especificado |
| E-F4 | Definir OKR y roadmap (gobierno) | Modelo OKR/roadmap | Especificado |
| E-F5 | Trazabilidad y checklist | Filas en matriz + `checklist.md` | Especificado |
| E-F6 | Revisión ejecutiva y aprobación | Acta de revisión | Pendiente por confirmar |

## Dependencias

- DWH y KPIs (CU-T10, CU-T11) deben estar especificados (nivel táctico).
- Fuentes de negocio (P09/P10/P11) y analítica (P04) disponibles como datos consolidados.
- Seguridad (P01) y auditoría (P03) operativas.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Métricas no estandarizadas | Tableros inconsistentes | Definir catálogo de KPIs (hecho en traceability) |
| Datos incompletos | Decisiones sesgadas | Mostrar cobertura y faltantes (FA-E1) |
| Sobre-alcance fuera de B2G | Violación de constitución | Revisión contra RN-03/RN-04 |

## Métricas de Éxito del Nivel

KPI-10 ARR/MRR, KPI-11 Precisión de forecast, KPI-03 Nº instituciones, KPI-07 Uptime%.

## Próximos Pasos

Tras aprobación, pasar a planificación de implementación con `/speckit-plan` por paquete (P12, P04).
