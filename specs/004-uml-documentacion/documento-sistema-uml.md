# Documento de Sistema UML — CrimeTrack Analytics Corp

> Documento UML textual del Sistema de Seguimiento, Gestión y Análisis de Crímenes (enfoque B2G).
> Subordinado a la constitución y a `000-sistema-general/`. **Sin implementación de código.**

## 1. Introducción

CrimeTrack Analytics Corp comercializa, bajo modelo **B2G**, un sistema que sus clientes
gubernamentales operan para la gestión y el análisis de crímenes, y que a la vez sostiene la
operación comercial de la empresa (adquisición, ecosistema de APIs, cloud e inteligencia de
negocio). Este documento describe la vista UML del sistema: actores, paquetes, casos de uso, sus
relaciones, el modelo de dominio inicial y las recomendaciones de diagramación. Todo elemento es
trazable a los objetivos estratégicos OE1–OE4 (inmutables).

## 2. Alcance UML del Sistema

- **Incluye:** 12 paquetes UML (P01–P12), 102 casos de uso (10 estratégicos, 16 tácticos, 76
  operativos —incluidos los **16 nuevos de auditoría CU-O61…CU-O76** del paquete P03), 14+1 actores
  (A01–A14, más A15 "Implementado adicional"), modelo de dominio inicial, **modelo de datos de
  auditoría** (sección 10.1) y relaciones paquete↔caso de uso↔actor.
- **Excluye:** implementación de código, diagramas gráficos finales (se entregan recomendaciones),
  dominios fuera de seguridad/justicia y cualquier alteración del alcance B2G u OE1–OE4.

## 3. Actores del Sistema

| Código | Actor | Descripción | Cara |
|---|---|---|---|
| A01 | Administrador del Sistema | Configura instituciones, usuarios, roles y parámetros. | Producto |
| A02 | Investigador Criminal | Gestiona expedientes e involucrados. | Producto |
| A03 | Analista Criminal | Usa analítica, mapas y tendencias. | Producto |
| A04 | Perito / Custodio de Evidencia | Registra y custodia evidencias. | Producto |
| A05 | Auditor / Oficial de Cumplimiento | Revisa auditoría y trazabilidad. | Producto |
| A06 | Usuario Institucional | Opera funciones según su rol. | Producto |
| A07 | Ejecutivo Corporativo / Dirección | Consume tableros y decide estrategia. | Negocio |
| A08 | Gerente Comercial B2G | Gestiona pipeline, contratos y propuestas. | Negocio |
| A09 | Especialista Growth / Marketing | Ejecuta campañas de adquisición. | Negocio |
| A10 | Ingeniero de Plataforma / SRE | Opera cloud, SLA y APIs. | Negocio |
| A11 | Analista de Inteligencia de Negocio | Administra DWH, KPIs y forecast. | Negocio |
| A12 | Customer Success Manager | Onboarding, soporte y retención. | Negocio |
| A13 | Cliente Institucional | Organización gubernamental (tenant). | Negocio |
| A14 | Sistema Externo / Integrador | Consume APIs y webhooks. | Negocio |
| A15 | Abogado / Especialista Legal & Contratos | RFP, contratos y licencias. (**Implementado adicional**) | Negocio |

## 4. Diagrama Textual de Paquetes UML

```text
CrimeTrack Analytics (Sistema B2G)
│
├── Núcleo de Producto (operación del cliente)
│   ├── P01 Autenticación y Seguridad
│   ├── P02 Administración del Sistema
│   ├── P03 Auditoría y Trazabilidad
│   ├── P04 Dashboard y Analítica Criminal
│   ├── P05 Gestión de Expedientes Criminales
│   ├── P06 Gestión de Evidencias Digitales
│   ├── P07 Gestión de Involucrados
│   └── P08 Reportería y Exportación
│
└── Núcleo de Negocio (operación de la empresa)
    ├── P09 Gestión Comercial B2G y Clientes Institucionales
    ├── P10 Ecosistema de APIs, Integraciones y Marketplace
    ├── P11 Gestión Cloud, SLA y Continuidad Operativa
    └── P12 Gobierno de Datos e Inteligencia de Negocio Corporativa

Dependencias clave:
P01 → habilita P02..P12 ;  P03 ← registra eventos de P01..P12
P05 → P06, P07 ;  P04 ← P05,P06,P07 ;  P08 ← P04..P07
P09,P10,P11 → P12 → alimenta Nivel Estratégico (CU-E01..E10)
```

## 5. Diagrama Textual de Casos de Uso (por actor y paquete)

```text
[A06 Usuario] ── CU-O01 Iniciar sesión ───────────────► (P01)
[A01 Admin]   ── CU-O06..O10 Administración ──────────► (P02)
[A05 Auditor] ── CU-O11..O15 Auditoría/Custodia ──────► (P03)
[A05/Sistema] ── CU-O61..O76 Auditoría total (NUEVO) ─► (P03 transversal a P01..P12)
[A03 Analista]── CU-O16..O20 Analítica criminal ──────► (P04)
[A02 Investig]── CU-O21..O25 Expedientes ─────────────► (P05)
[A04 Custodio]── CU-O26..O30 Evidencias ──────────────► (P06)
[A02 Investig]── CU-O31..O35 Involucrados ────────────► (P07)
[A06 Usuario] ── CU-O36..O40 Reportería ──────────────► (P08)
[A08 Comercial]─ CU-O41..O45 Comercial B2G ───────────► (P09)
[A10 SRE/A14]  ─ CU-O46..O50 APIs/Integraciones ──────► (P10)
[A10 SRE]      ─ CU-O51..O55 Cloud/SLA ───────────────► (P11)
[A11 BI]       ─ CU-O56..O60 Datos e Inteligencia ────► (P12)
[A08/A09]      ─ CU-T01..T16 Tácticos ────────────────► (P09,P10,P11,P12,P02,P03)
[A07 Ejecutivo]─ CU-E01..E10 Estratégicos ────────────► (P12,P04,P09,P10,P11,P08)
```

## 6. Relación de Paquetes con Casos de Uso

| Paquete | Casos de uso |
|---|---|
| P01 | CU-O01, CU-O02, CU-O03, CU-O04, CU-O05 |
| P02 | CU-O06, CU-O07, CU-O08, CU-O09, CU-O10; (CU-T08, CU-T14 parcial) |
| P03 | CU-O11, CU-O12, CU-O13, CU-O14, CU-O15; **CU-O61…CU-O76 (NIVEL AUDITORÍA, nuevos)**; (CU-T12) |
| P04 | CU-O16, CU-O17, CU-O18, CU-O19, CU-O20; (CU-T11, CU-E01) |
| P05 | CU-O21, CU-O22, CU-O23, CU-O24, CU-O25 |
| P06 | CU-O26, CU-O27, CU-O28, CU-O29, CU-O30 |
| P07 | CU-O31, CU-O32, CU-O33, CU-O34, CU-O35 |
| P08 | CU-O36, CU-O37, CU-O38, CU-O39, CU-O40; (CU-E08) |
| P09 | CU-O41..CU-O45; CU-T01..T04, CU-T13..T16; (CU-E02, CU-E09) |
| P10 | CU-O46..CU-O50; CU-T05, CU-T06, CU-T07; (CU-E07) |
| P11 | CU-O51..CU-O55; CU-T09; (CU-E06) |
| P12 | CU-O56..CU-O60; CU-T10, CU-T11; CU-E01, CU-E03, CU-E04, CU-E05, CU-E08, CU-E10 |

## 7. Relación de Casos de Uso con Actores

| Actor | Casos de uso (principales) |
|---|---|
| A01 Administrador | CU-O06, CU-O07, CU-O08, CU-O09, CU-O22, CU-O25, CU-T08 |
| A02 Investigador | CU-O21–CU-O25, CU-O30–CU-O36 |
| A03 Analista Criminal | CU-O16–CU-O20, CU-O35 |
| A04 Custodio | CU-O15, CU-O26–CU-O30 |
| A05 Auditor | CU-O11–CU-O15, **CU-O61–CU-O76 (auditoría total)**, CU-T12 |
| A06 Usuario Institucional | CU-O01–CU-O05, CU-O36–CU-O40 |
| A07 Ejecutivo | CU-E01–CU-E10, CU-O59 |
| A08 Gerente Comercial | CU-O41–CU-O45, CU-T02–CU-T04, CU-T07, CU-T13, CU-T14 |
| A09 Especialista Growth | CU-O41, CU-T01 |
| A10 SRE | CU-O46–CU-O55, CU-T05, CU-T06, CU-T09 |
| A11 Analista BI | CU-O56–CU-O60, CU-T10, CU-T11 |
| A12 Customer Success | CU-T15, CU-T16 |
| A13 Cliente Institucional | (beneficiario) CU-O06, CU-O39, CU-O40 |
| A14 Sistema Externo | CU-O46–CU-O50, CU-T06 |
| A15 Legal & Contratos | CU-T04, CU-T14, CU-O44 |

## 8. Descripción de Cada Paquete UML

Ver detalle ampliado en `paquetes-uml.md`. Resumen:

- **P01** identidad, MFA, sesiones, RBAC. **P02** instituciones, usuarios, parámetros, licencias,
  contratos. **P03** auditoría y trazabilidad **total y centralizada** (CU-O11…O15 + CU-O61…O76):
  registro append-only de toda operación (CRUD, auth/sesiones, RBAC, acceso sensible, expedientes,
  evidencias/custodia, involucrados, exportaciones, configuración, APIs, cloud, BI) con hash
  encadenado, alertas, verificación de integridad, retención/archivado y tablero/ reportes de
  cumplimiento (ver `003-operativo/P03-auditoria/`). **P04** mapa de calor,
  indicadores, tendencias, predicción. **P05** ciclo de vida de expedientes. **P06** evidencias y
  cadena de custodia. **P07** involucrados. **P08** reportería y exportación. **P09** comercial
  B2G. **P10** APIs, integraciones y marketplace. **P11** cloud, SLA y continuidad. **P12**
  gobierno de datos e inteligencia de negocio.

## 9. Descripción de Cada Caso de Uso

El detalle completo (actor, objetivo, precondición, flujo principal, flujo alternativo y criterio
de aceptación) de los 102 casos de uso está en `casos-uso.md`. Los **16 casos de uso nuevos de
auditoría (CU-O61…CU-O76)** se documentan allí con la estructura ampliada de 18 puntos en la
sección "CASOS DE USO NUEVOS — NIVEL AUDITORÍA (P03)". Este documento referencia esa fuente para
evitar duplicación y mantener una única verdad por caso de uso.

## 10. Modelo de Dominio Inicial

Entidades principales y relaciones (conceptual, sin esquema físico):

```text
Institucion (tenant) 1───* Usuario *───* Rol *───* Permiso
Institucion 1───* Contrato 1───* Licencia ; Contrato 1───1 SLA
Usuario 1───* SesionActiva ; Usuario 1───* RegistroAuditoria
Expediente 1───* Involucrado(Victima|Sospechoso|Testigo)
Expediente 1───* Evidencia 1───1 Hash ; Evidencia 1───* EventoCustodia
Expediente *───* Delito ; Expediente 1───* Reporte
Lead 1───1 Oportunidad 1───* ActividadComercial ; Oportunidad 1───1 Propuesta
APIKey 1───* ConsumoAPI ; Integracion 1───* Webhook/Conector
FuenteDatos *───1 DataWarehouse 1───* KPI 1───* Tablero ; Tablero 1───* Forecast/Benchmark
ServicioCloud 1───* MetricaUptime ; ServicioCloud 1───* IncidenteSLA ; Backup, PlanDR
```

Reglas de dominio destacadas: toda `Evidencia` mantiene `EventoCustodia` inmutables (RN-02); toda
operación relevante crea `RegistroAuditoria` (RN-05); las capacidades visibles dependen de
`Contrato`/`Licencia` (RN-07); cada `Institucion` aísla sus datos (RN-06).

## 10.1 Modelo de Datos de Auditoría (P03 ampliado)

Modelo centralizado **append-only** con `event_hash`/`previous_hash` encadenado. La tabla central
`audit_events` se relaciona con tablas satélite. Diseño y decisión de almacenamiento (PostgreSQL
append-only vs MinIO WORM, **PC-A1**) en `003-operativo/P03-auditoria/spec.md`.

```text
audit_events (central, append-only, hash-chain)
  ├─1──*─ audit_event_changes (valor_anterior / valor_nuevo / diff, enmascarado)
  ├─1──*─ audit_access_events  (acceso a info sensible: consulta/descarga/exportación…)
  ├─1──*─ audit_exports        (reportes/exportaciones: formato, motivo, marca de agua)
  └─1──*─ audit_api_events     (APIs/webhooks: endpoint, código, latencia; SIN secretos)
audit_sessions        (inicio, última actividad, cierre, duración, IP, dispositivo, MFA)
audit_evidence_events (hash inicial/recalculo, verificación) ─┐
audit_custody_events  (custodio anterior/nuevo, motivo, ruptura)┘─ habilitan CU-O15
audit_security_alerts (tipo, severidad, responsable, acción, cierre)
audit_integrity_checks(verificación periódica de la cadena de hash)
audit_retention_policies (retención por institución) ─1──*─ audit_archives (históricos)
```

Reglas: logs **append-only** (ningún rol altera el historial), tiempo en **servidor/UTC**, hash por
evento, **enmascaramiento** de datos sensibles, **sin** contraseñas/tokens/secretos/API keys
completas, aislamiento **multi-tenant** y solo Auditor/Compliance consulta auditoría completa.

## 11. Recomendación de Diagramas UML

Diagramas sugeridos (legibles y proporcionados, RI-04; sin miniaturas):

1. **Diagrama de paquetes** (P01–P12 con dependencias) — visión arquitectónica.
2. **Diagramas de casos de uso por paquete** (uno por P01–P12) — evita sobrecargar un solo lienzo.
3. **Diagrama de casos de uso por nivel** (estratégico, táctico, operativo).
4. **Diagrama de clases del modelo de dominio** (entidades de la sección 10).
5. **Diagramas de secuencia** para flujos críticos: CU-O01 (login+MFA), CU-O26→O28 (evidencia+hash),
   CU-O25 (cierre de expediente), CU-O55 (DR), **CU-O61 (captura de auditoría vía middleware +
   decorador → AuditService → hash-chain)** y **CU-O75 (verificación de integridad)**.
6. **Diagrama de estados** del `Expediente` (abierto→en investigación→cerrado/reabierto).
7. **Diagrama de actividad** para CU-O36/CU-O37 (generación y exportación de reportes).
8. **Diagrama de despliegue** para la arquitectura cloud de alta disponibilidad (OE3).

Herramientas recomendadas: PlantUML o Mermaid (texto→diagrama, versionable junto a estas specs).

## 12. Casos de Uso Recomendados para Demostrar en Video

| CU | Nombre | Por qué demostrarlo |
|---|---|---|
| CU-O01 | Iniciar sesión | Seguridad base y MFA |
| CU-O21 | Crear expediente criminal | Núcleo del producto |
| CU-O26 | Registrar evidencia digital | Cadena de custodia + hash |
| CU-O31 | Registrar víctima | Gestión de involucrados |
| CU-O32 | Registrar sospechoso | Gestión de involucrados |
| CU-O36 | Generar reporte operativo | Valor de salida |
| CU-O37 | Exportar reporte PDF/Excel | Entregable formal |
| CU-O16 | Visualizar mapa de calor criminal | Analítica visual (OE4) |

Detalle del guion y la lista en `../005-entrega-video/`.

## Pendientes por Confirmar

- **PC-U1:** Validar el modelo de dominio con el equipo de producto (cardinalidades finas).
- **PC-U2:** Confirmar herramienta oficial de diagramación (PlantUML vs Mermaid).
