# Especificación — Nivel Táctico

> Nivel empresarial **Táctico**. Casos de uso CU-T01…CU-T16. Subordinada a la constitución y a
> `000-sistema-general/`. **Sin implementación de código.**

## 1. Objetivo

Especificar las capacidades de ejecución de mediano plazo que traducen los objetivos estratégicos
(OE1–OE4) en operación: campañas de adquisición, pipeline, demos, licitaciones, catálogo de APIs,
integraciones, marketplace, roles institucionales, SLA, data warehouse, KPIs, auditoría/cumplimiento,
paquetes de producto, contratos, onboarding y soporte.

## 2. Contexto

El nivel táctico configura y coordina los recursos que el nivel operativo ejecuta a diario y que el
nivel estratégico mide. Es el puente entre la dirección (001) y la operación (003).

## 3. Actores

A08 Gerente Comercial B2G, A09 Especialista Growth, A10 Ingeniero de Plataforma/SRE, A11 Analista BI,
A01 Administrador, A05 Auditor/Cumplimiento, A12 Customer Success, A15 Legal & Contratos, A14 Sistema Externo.

## 4. Departamento Responsable

D02 Comercial & Growth, D03 Producto & Plataforma, D04 Operaciones Cloud, D05 BI, D06 Seguridad &
Cumplimiento, D08 Customer Success, D09 Legal & Contratos.

## 5. Nivel Empresarial

Táctico.

## 6. Paquete UML Relacionado

P09 Comercial B2G, P10 Ecosistema de APIs, P11 Cloud y SLA, P12 Gobierno de Datos e BI, P04 Analítica,
P02 Administración, P01 Seguridad, P03 Auditoría.

## 7. Objetivos Relacionados

| OE | OT | Casos de uso tácticos asociados |
|---|---|---|
| OE1 | OT1 | CU-T01, CU-T02, CU-T03, CU-T04, CU-T13, CU-T14, CU-T15, CU-T16 |
| OE2 | OT2 | CU-T05, CU-T06, CU-T07 |
| OE3 | OT3 | CU-T09 |
| OE4 | OT4 | CU-T10, CU-T11 |
| OE1–OE4 | OT5 | CU-T08, CU-T12 |

## 8. Requisitos Funcionales

| ID | Requisito | CU |
|---|---|---|
| RF-T-01 | Gestionar campañas de Growth Hacking B2G (crear, segmentar, medir) | CU-T01 |
| RF-T-02 | Administrar el pipeline institucional (etapas, oportunidades) | CU-T02 |
| RF-T-03 | Gestionar demos y pruebas piloto | CU-T03 |
| RF-T-04 | Gestionar licitaciones y RFP (avances, documentos) | CU-T04 |
| RF-T-05 | Configurar el catálogo de APIs | CU-T05 |
| RF-T-06 | Gestionar integraciones con sistemas externos | CU-T06 |
| RF-T-07 | Gestionar marketplace y planes SaaS | CU-T07 |
| RF-T-08 | Configurar roles y permisos institucionales | CU-T08 |
| RF-T-09 | Gestionar SLA y monitoreo cloud | CU-T09 |
| RF-T-10 | Gestionar el data warehouse corporativo | CU-T10 |
| RF-T-11 | Configurar indicadores KPI y tableros | CU-T11 |
| RF-T-12 | Gestionar auditoría y cumplimiento | CU-T12 |
| RF-T-13 | Gestionar paquetes de producto por cliente | CU-T13 |
| RF-T-14 | Administrar contratos y licencias B2G | CU-T14 |
| RF-T-15 | Gestionar onboarding y capacitación institucional | CU-T15 |
| RF-T-16 | Gestionar soporte postventa y customer success | CU-T16 |

## 9. Requisitos No Funcionales

| ID | Requisito |
|---|---|
| RNF-T-01 | Configuraciones versionadas y auditadas. |
| RNF-T-02 | Cambios de roles/permisos con doble control y MFA (RS-04). |
| RNF-T-03 | Catálogo de APIs documentado y versionado (OE2). |
| RNF-T-04 | Monitoreo de SLA con alertas en tiempo casi real (OE3). |
| RNF-T-05 | DWH con calidad y linaje de datos (gobierno de datos). |

## 10. Reglas de Negocio

RN-01, RN-03, RN-04, RN-06 (multi-tenant), RN-07 (capacidades por contrato), RN-10 (APIs).

## 11. Entradas

Definiciones de campañas, leads y oportunidades; documentos de licitación; especificaciones de APIs;
configuración de integraciones; planes SaaS; matrices de roles; umbrales de SLA; fuentes para DWH;
definiciones de KPI; contratos y licencias.

## 12. Salidas

Campañas activas, pipeline actualizado, catálogo de APIs publicado, integraciones configuradas,
planes en marketplace, roles institucionales, SLA monitoreado, DWH poblado, KPIs/tableros, paquetes
por cliente, contratos vigentes, onboarding ejecutado, casos de soporte.

## 13. Precondiciones

Usuarios tácticos autenticados (MFA donde aplica); institución cliente registrada; capa operativa y
de seguridad disponible.

## 14. Flujo Principal

1. El responsable táctico selecciona la capacidad a configurar/gestionar.
2. Define parámetros (campaña, API, plan, rol, SLA, KPI, contrato, etc.).
3. El sistema valida reglas (contrato, permisos, tenant) y persiste con auditoría.
4. La configuración queda disponible para la operación (003) y medible por estrategia (001).

## 15. Flujos Alternativos

- **FA-T1:** capacidad no incluida en contrato → bloqueada (RN-07).
- **FA-T2:** integración externa requiere credenciales → flujo de aprovisionamiento seguro.

## 16. Excepciones

- **EX-T1:** API mal versionada → rechazo de publicación.
- **EX-T2:** umbral de SLA inconsistente → validación y aviso.

## 17. Criterios de Aceptación (Dado / Cuando / Entonces)

- **CA-T-01** — Dado un gerente comercial, Cuando crea una campaña Growth B2G, Entonces queda
  registrada, segmentada y medible por KPI-02.
- **CA-T-02** — Dado un administrador, Cuando configura roles institucionales, Entonces los permisos
  se aplican con privilegio mínimo y quedan auditados.
- **CA-T-03** — Dado un SRE, Cuando define umbrales de SLA, Entonces el monitoreo genera alertas al
  incumplirse (KPI-08).
- **CA-T-04** — Dada una API nueva, Cuando se publica en el catálogo, Entonces queda versionada y
  documentada (OE2).

## 18. Dependencias

Nivel operativo (003) para ejecución; P01/P02/P03 (seguridad, admin, auditoría); P12 (DWH/KPI).

## 19. Fuera de Alcance

Decisiones estratégicas (001); operación diaria de expedientes/evidencias (003). Modificación de OE.

## 20. Historias de Usuario Relacionadas

HU-T-01…HU-T-16 (ver `004-uml-documentacion/historias-usuario.md`).

## Pendientes por Confirmar

- **PC-T3:** Estándar de especificación de APIs (OpenAPI u otro) y política de versionado.
- **PC-T4:** Matriz fina de roles/permisos institucionales por tipo de cliente.
