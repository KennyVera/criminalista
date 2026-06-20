# Especificación General del Sistema — CrimeTrack Analytics Corp

> Documento raíz de la estructura de especificaciones (Spec-Driven Development).
> Fuente de verdad subordinada a `.specify/memory/constitution.md`.
> **No contiene implementación de código.** Solo documentación y especificación.

| Metadato | Valor |
|---|---|
| Proyecto | CrimeTrack Analytics Corp |
| Sistema | Sistema de Seguimiento, Gestión y Análisis de Crímenes |
| Enfoque | Empresarial **B2G** (Business-to-Government) |
| Versión spec | 1.0.0 |
| Estado | Borrador para revisión (pre-implementación) |
| Fecha | 2026-06-20 |

---

## 1. Objetivo

Definir, de forma integral y trazable, **qué** debe ser el Sistema de Seguimiento, Gestión y
Análisis de Crímenes de CrimeTrack Analytics Corp, considerando su naturaleza **empresarial
B2G**: una plataforma comercializable a ministerios de seguridad, instituciones policiales,
departamentos de investigación criminal y organismos gubernamentales.

El sistema persigue, sin alteración, los cuatro Objetivos Estratégicos (OE) obligatorios:

- **OE1 — Penetración de Mercado Digital y Adquisición Automatizada de Clientes (Growth Hacking B2G).**
- **OE2 — Escalabilidad Comercial Exponencial a través de Plataformas de Ecosistemas, Marketplaces y APIs.**
- **OE3 — Expansión Continua Basada en Infraestructura en la Nube de Alta Disponibilidad.**
- **OE4 — Inteligencia de Negocio Centralizada para la Ventaja Competitiva Global.**

## 2. Contexto

CrimeTrack Analytics Corp **desarrolla y comercializa** el sistema; sus clientes son organismos
gubernamentales que lo operan para gestión criminalística. Por ello el producto tiene dos caras
indivisibles:

- **Cara de producto (operación criminalística del cliente):** autenticación, expedientes,
  evidencias, involucrados, analítica criminal, reportería, auditoría y cadena de custodia.
- **Cara de negocio (operación comercial de la empresa):** adquisición automatizada B2G,
  ecosistema de APIs/marketplace, operación cloud con SLA e inteligencia de negocio centralizada.

La plataforma es **multi-tenant / multi-institución**, con aislamiento de datos por cliente y
cumplimiento normativo por jurisdicción. Esta especificación general establece el marco común;
las especificaciones por nivel (001 estratégico, 002 táctico, 003 operativo) y la documentación
UML (004) lo detallan.

## 3. Actores

| Código | Actor | Tipo | Cara |
|---|---|---|---|
| A01 | Administrador del Sistema | Humano | Producto |
| A02 | Investigador Criminal | Humano | Producto |
| A03 | Analista Criminal | Humano | Producto |
| A04 | Perito / Custodio de Evidencia | Humano | Producto |
| A05 | Auditor / Oficial de Cumplimiento | Humano | Producto |
| A06 | Usuario Institucional (operativo) | Humano | Producto |
| A07 | Ejecutivo Corporativo / Dirección | Humano | Negocio |
| A08 | Gerente Comercial B2G | Humano | Negocio |
| A09 | Especialista Growth / Marketing | Humano | Negocio |
| A10 | Ingeniero de Plataforma / SRE (DevOps) | Humano | Negocio |
| A11 | Analista de Inteligencia de Negocio (BI) | Humano | Negocio |
| A12 | Customer Success Manager | Humano | Negocio |
| A13 | Cliente Institucional (organización) | Organización | Negocio |
| A14 | Sistema Externo / Integrador (consumidor de API) | Sistema | Negocio |

## 4. Departamento Responsable

| Código | Departamento | Nivel principal |
|---|---|---|
| D01 | Dirección Ejecutiva y Estrategia Corporativa | Estratégico |
| D02 | Comercial & Growth B2G | Táctico/Operativo |
| D03 | Producto & Plataforma (Ingeniería) | Táctico/Operativo |
| D04 | Operaciones Cloud & SRE | Táctico/Operativo |
| D05 | Inteligencia de Negocio (BI) | Estratégico/Táctico |
| D06 | Seguridad & Cumplimiento | Transversal |
| D07 | Operaciones Criminalísticas (cliente) | Operativo |
| D08 | Customer Success & Soporte | Táctico/Operativo |
| D09 | Legal & Contratos | Táctico |

## 5. Nivel Empresarial

El sistema se estructura en tres niveles, cada uno con su especificación dedicada:

- **Estratégico (`001-estrategico/`):** dirección corporativa, OKR, Balanced Scorecard, ventaja
  competitiva, roadmap. Casos de uso CU-E01…CU-E10.
- **Táctico (`002-tactico/`):** ejecución de campañas, pipeline, APIs, marketplace, SLA, data
  warehouse, cumplimiento. Casos de uso CU-T01…CU-T16.
- **Operativo (`003-operativo/`):** operación diaria del producto y del negocio. Casos de uso
  CU-O01…CU-O60.

## 6. Paquete UML Relacionado

Doce paquetes UML obligatorios (detalle en `004-uml-documentacion/paquetes-uml.md`):

| Paquete | Nombre | Cara |
|---|---|---|
| P01 | Autenticación y Seguridad | Producto |
| P02 | Administración del Sistema | Producto |
| P03 | Auditoría y Trazabilidad | Producto |
| P04 | Dashboard y Analítica Criminal | Producto |
| P05 | Gestión de Expedientes Criminales | Producto |
| P06 | Gestión de Evidencias Digitales | Producto |
| P07 | Gestión de Involucrados | Producto |
| P08 | Reportería y Exportación | Producto |
| P09 | Gestión Comercial B2G y Clientes Institucionales | Negocio |
| P10 | Ecosistema de APIs, Integraciones y Marketplace | Negocio |
| P11 | Gestión Cloud, SLA y Continuidad Operativa | Negocio |
| P12 | Gobierno de Datos e Inteligencia de Negocio Corporativa | Negocio |

## 7. Objetivos Relacionados (Estratégico / Táctico / Operativo)

Cadena de objetivos (detalle y matriz en `traceability.md`):

| OE | Objetivo Táctico (OT) | Objetivo Operativo (OP) — paquete |
|---|---|---|
| OE1 Growth B2G | OT1 Adquisición y pipeline automatizado | OP9 (P09) |
| OE2 Ecosistemas/APIs | OT2 Operar ecosistema de APIs y marketplace | OP10 (P10) |
| OE3 Cloud HA | OT3 Disponibilidad, escalabilidad y continuidad | OP11 (P11) |
| OE4 Inteligencia de Negocio | OT4 Centralizar datos e inteligencia | OP12 (P12), OP4 (P04) |
| Transversal (habilita OE1–OE4) | OT5 Gobierno, seguridad y cumplimiento | OP1 (P01), OP2 (P02), OP3 (P03) |
| Producto vendible (habilita OE1, OE2, OE4) | OT6 Excelencia criminalística del producto | OP5–OP8 (P05–P08) |

> El núcleo criminalístico (P04–P08) es el **producto** que se comercializa: su calidad alimenta
> directamente OE4 (datos→inteligencia) y sustenta OE1/OE2 (valor vendible). Ningún objetivo
> queda huérfano.

## 8. Requisitos Funcionales (nivel sistema)

| ID | Requisito |
|---|---|
| RF-SYS-01 | El sistema debe autenticar usuarios y autorizar acciones por rol (RBAC) con privilegio mínimo. |
| RF-SYS-02 | El sistema debe ser multi-tenant, aislando datos por institución cliente. |
| RF-SYS-03 | El sistema debe registrar auditoría inmutable de eventos relevantes. |
| RF-SYS-04 | El sistema debe gestionar el ciclo de vida de expedientes, evidencias e involucrados. |
| RF-SYS-05 | El sistema debe preservar la cadena de custodia íntegra de las evidencias. |
| RF-SYS-06 | El sistema debe ofrecer analítica criminal (indicadores, mapas, tendencias, predicción). |
| RF-SYS-07 | El sistema debe generar reportería e informes exportables (PDF/Excel) autorizados. |
| RF-SYS-08 | El sistema debe soportar la operación comercial B2G (leads, pipeline, propuestas, contratos). |
| RF-SYS-09 | El sistema debe exponer un ecosistema de APIs versionadas con marketplace e integraciones. |
| RF-SYS-10 | El sistema debe operar sobre cloud de alta disponibilidad con SLA y continuidad. |
| RF-SYS-11 | El sistema debe consolidar datos e inteligencia de negocio (KPI, tableros, forecast). |
| RF-SYS-12 | El sistema debe mantener trazabilidad requisito↔caso de uso↔objetivo en todo momento. |

## 9. Requisitos No Funcionales (nivel sistema)

| ID | Categoría | Requisito |
|---|---|---|
| RNF-SYS-01 | Disponibilidad | Uptime objetivo ≥ 99.9% (OE3); arquitectura redundante. |
| RNF-SYS-02 | Escalabilidad | Escalamiento horizontal/elástico ante demanda (OE3). |
| RNF-SYS-03 | Seguridad | Cifrado en tránsito y reposo; MFA para roles críticos; hashing fuerte de credenciales. |
| RNF-SYS-04 | Auditabilidad | Logs inmutables, atribuibles y exportables. |
| RNF-SYS-05 | Rendimiento | Respuestas interactivas < 2 s en operaciones comunes; reportes asíncronos si son pesados. |
| RNF-SYS-06 | Cumplimiento | Conformidad normativa por jurisdicción; soberanía de datos. |
| RNF-SYS-07 | Mantenibilidad | Modularidad por paquetes UML; bajo acoplamiento; documentación previa. |
| RNF-SYS-08 | Interoperabilidad | APIs estándar, versionadas y documentadas (OE2). |
| RNF-SYS-09 | Usabilidad | Interfaces claras; gráficos legibles y proporcionados (sin miniaturas ilegibles). |
| RNF-SYS-10 | Continuidad | Respaldos programados; RTO/RPO definidos; recuperación ante desastres (OE3). |

## 10. Reglas de Negocio

Las reglas de negocio comunes se centralizan en `rules.md`. A nivel sistema destacan:
RN-01 (no funcionalidad sin trazabilidad estratégica), RN-02 (cadena de custodia inviolable),
RN-03 (alcance B2G inmutable), RN-04 (OE1–OE4 inmutables), RN-05 (auditoría obligatoria).

## 11. Entradas

Credenciales y solicitudes de usuarios autenticados; datos de instituciones cliente; datos
criminalísticos (expedientes, evidencias, involucrados); datos comerciales (leads, contratos);
llamadas y eventos de APIs/integraciones; métricas de infraestructura cloud; parámetros y
catálogos de configuración.

## 12. Salidas

Vistas y tableros (criminalísticos y de negocio); expedientes y registros con cadena de custodia;
reportes e informes PDF/Excel; respuestas de API y webhooks; KPIs, benchmarks y forecasts;
registros de auditoría exportables; alertas y notificaciones.

## 13. Precondiciones

Usuario autenticado y autorizado; institución cliente registrada y activa; configuración de
parámetros y catálogos cargada; servicios cloud disponibles; contratos/licencias vigentes para
las capacidades comerciales.

## 14. Flujo Principal (nivel sistema)

1. El cliente institucional es registrado y aprovisionado (contrato, licencia, SLA).
2. Los usuarios se autentican (con MFA cuando aplica) y operan según su rol.
3. La operación criminalística genera datos (expedientes, evidencias, involucrados) con auditoría
   y cadena de custodia.
4. La analítica y la reportería transforman datos en conocimiento accionable.
5. La operación de negocio (comercial, APIs, cloud, BI) sostiene la adquisición, escalabilidad,
   disponibilidad e inteligencia.
6. La inteligencia de negocio centralizada retroalimenta la estrategia (OE1–OE4).

## 15. Flujos Alternativos

- **FA-1:** institución sin contrato vigente → acceso restringido a capacidades contratadas.
- **FA-2:** rol sin permiso → acción denegada y registrada en auditoría.
- **FA-3:** consumo por API en lugar de UI → mismas reglas de seguridad y trazabilidad.

## 16. Excepciones

- **EX-1:** fallo de autenticación → bloqueo/registro; aplica política de intentos.
- **EX-2:** indisponibilidad de servicio cloud → activación de continuidad/DR (P11).
- **EX-3:** intento de manipulación de evidencia → alerta y preservación de cadena de custodia (P03/P06).

## 17. Criterios de Aceptación (Dado / Cuando / Entonces)

- **CA-SYS-01** — Dado un usuario no autenticado, Cuando intenta acceder a un recurso protegido,
  Entonces el sistema lo deniega y registra el intento.
- **CA-SYS-02** — Dado un evento sobre datos delictivos, Cuando ocurre, Entonces queda un registro
  de auditoría inmutable, atribuible y con marca temporal.
- **CA-SYS-03** — Dada una evidencia digital, Cuando se registra o transfiere, Entonces su cadena
  de custodia se mantiene íntegra y verificable.
- **CA-SYS-04** — Dada cualquier funcionalidad, Cuando se especifica, Entonces existe su enlace
  trazable hasta al menos un OE (OE1–OE4).

## 18. Dependencias

Constitución (`.specify/memory/constitution.md`); especificaciones de nivel (001/002/003);
documentación UML (004); infraestructura cloud (OE3); proveedor de identidad y MFA.

## 19. Fuera de Alcance

- Implementación de código (esta fase es solo documentación/especificación).
- Dominios ajenos a seguridad/justicia o que rompan el alcance B2G.
- Modificación de OE1–OE4.
- Hardware físico forense y procesos de laboratorio fuera del sistema digital.

## 20. Historias de Usuario Relacionadas

Catálogo completo en `004-uml-documentacion/historias-usuario.md` (HU-E-*, HU-T-*, HU-O-*).
Toda historia se asocia a un caso de uso y a un objetivo operativo, y remonta a un OE.

---

## Pendientes por Confirmar

- **PC-01:** Normativas/jurisdicciones concretas a cumplir por cliente (p. ej., leyes locales de
  protección de datos y de evidencia digital).
- **PC-02:** Valores exactos de SLA contractual (uptime, RTO, RPO) por plan comercial.
- **PC-03:** Política de retención y soberanía de datos por país.
- **PC-04:** Proveedores de identidad/MFA y de nube de referencia.
- **PC-05:** Catálogo de planes SaaS y precios del marketplace.
