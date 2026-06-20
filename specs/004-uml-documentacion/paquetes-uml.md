# Paquetes UML — CrimeTrack Analytics Corp

> Doce paquetes UML obligatorios (P01–P12). Cada paquete agrupa casos de uso cohesivos con una
> responsabilidad clara y contratos explícitos. Subordinado a la constitución y a `000-sistema-general/`.

## Vista General

| Paquete | Nombre | Cara | OP | OT | OE | Departamento |
|---|---|---|---|---|---|---|
| P01 | Autenticación y Seguridad | Producto | OP1 | OT5 | habilitador OE1–OE4 | D06 |
| P02 | Administración del Sistema | Producto | OP2 | OT5 | habilitador OE1–OE4 | D01/D06 |
| P03 | Auditoría y Trazabilidad | Producto | OP3 | OT5 | habilitador OE1–OE4 | D06 |
| P04 | Dashboard y Analítica Criminal | Producto | OP4 | OT4 | OE4 | D07/D05 |
| P05 | Gestión de Expedientes Criminales | Producto | OP5 | OT6 | OE1/OE2/OE4 | D07 |
| P06 | Gestión de Evidencias Digitales | Producto | OP6 | OT6 | OE1/OE2/OE4 | D07/D06 |
| P07 | Gestión de Involucrados | Producto | OP7 | OT6 | OE1/OE2/OE4 | D07 |
| P08 | Reportería y Exportación | Producto | OP8 | OT6 | OE1/OE2/OE4 | D07 |
| P09 | Gestión Comercial B2G y Clientes Institucionales | Negocio | OP9 | OT1 | OE1 | D02 |
| P10 | Ecosistema de APIs, Integraciones y Marketplace | Negocio | OP10 | OT2 | OE2 | D03 |
| P11 | Gestión Cloud, SLA y Continuidad Operativa | Negocio | OP11 | OT3 | OE3 | D04 |
| P12 | Gobierno de Datos e Inteligencia de Negocio Corporativa | Negocio | OP12 | OT4 | OE4 | D05 |

## Descripción por Paquete

### P01 — Autenticación y Seguridad
**Responsabilidad:** identidad, acceso y control de permisos. **Casos de uso:** CU-O01..O05.
**Provee a:** todos los paquetes (acceso seguro). **Depende de:** proveedor de identidad/MFA.

### P02 — Administración del Sistema
**Responsabilidad:** alta y configuración de instituciones, usuarios/roles, parámetros, licencias,
contratos/SLA. **Casos de uso:** CU-O06..O10. **Depende de:** P01.

### P03 — Auditoría y Trazabilidad
**Responsabilidad:** bitácoras, trazabilidad de actividad, exportación de logs, alertas de
manipulación y validación de cadena de custodia. **Casos de uso:** CU-O11..O15. **Depende de:** P01.

### P04 — Dashboard y Analítica Criminal
**Responsabilidad:** mapa de calor, indicadores, filtros, tendencias y predicción. **Casos de uso:**
CU-O16..O20. **Depende de:** P05–P07 (datos), P12 (consolidación).

### P05 — Gestión de Expedientes Criminales
**Responsabilidad:** ciclo de vida del expediente. **Casos de uso:** CU-O21..O25. **Depende de:**
P01, P02; relaciona P06 y P07.

### P06 — Gestión de Evidencias Digitales
**Responsabilidad:** registro, carga, hash, custodia y consulta de evidencias. **Casos de uso:**
CU-O26..O30. **Depende de:** P05, P03 (custodia/auditoría).

### P07 — Gestión de Involucrados
**Responsabilidad:** víctimas, sospechosos, testigos y su vínculo con expedientes. **Casos de uso:**
CU-O31..O35. **Depende de:** P05.

### P08 — Reportería y Exportación
**Responsabilidad:** generación, exportación (PDF/Excel), programación, emisión y envío de reportes.
**Casos de uso:** CU-O36..O40. **Depende de:** P04–P07, P03.

### P09 — Gestión Comercial B2G y Clientes Institucionales
**Responsabilidad:** captación y gestión comercial (leads, oportunidades, demos, RFP, propuestas,
paquetes, contratos, onboarding, soporte). **Casos de uso:** CU-O41..O45 (operativos) + CU-T01..T04,
T13..T16. **Depende de:** P02.

### P10 — Ecosistema de APIs, Integraciones y Marketplace
**Responsabilidad:** API keys, documentación, webhooks, consumo, conectores, marketplace.
**Casos de uso:** CU-O46..O50 + CU-T05..T07. **Depende de:** P01.

### P11 — Gestión Cloud, SLA y Continuidad Operativa
**Responsabilidad:** uptime, backups, escalamiento, incidentes SLA y recuperación ante desastres.
**Casos de uso:** CU-O51..O55 + CU-T09. **Depende de:** infraestructura cloud.

### P12 — Gobierno de Datos e Inteligencia de Negocio Corporativa
**Responsabilidad:** consolidación de datos, KPIs, benchmark, tableros ejecutivos y forecast.
**Casos de uso:** CU-O56..O60 + CU-T10..T11 + CU-E01..E10 (consumo). **Depende de:** P04, P09–P11.

## Diagrama Textual de Dependencias entre Paquetes

```text
P01 Seguridad ──► (habilita) ──► P02 P03 P04 P05 P06 P07 P08 P09 P10 P11 P12
P02 Admin ──► P05 P09 P10
P03 Auditoría ◄── (registra eventos de) ── P01..P12
P05 Expedientes ──► P06 Evidencias
                └─► P07 Involucrados
P04 Analítica ◄── P05 P06 P07
P08 Reportería ◄── P04 P05 P06 P07
P09 Comercial ──► P12
P10 APIs ──► P12
P11 Cloud/SLA ──► P12
P12 BI ◄── P04 P09 P10 P11 ──► (alimenta) ──► Nivel Estratégico (CU-E01..E10)
```

## Estado de Paquetes

Todos los paquetes P01–P12 están **Especificados** (sin código). No se detectaron paquetes
faltantes; si surgiera uno, se agregará con estado **"Implementado adicional"**.
