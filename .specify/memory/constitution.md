# Constitución del Proyecto CrimeTrack Analytics Corp

> Sistema de Seguimiento, Gestión y Análisis de Crímenes — Enfoque empresarial B2G.
> Este documento es la fuente de verdad para el desarrollo dirigido por especificaciones
> (Spec-Driven Development). Toda especificación, plan, tarea, código y entregable debe
> cumplir y poder trazarse contra esta constitución.

## Contexto del Proyecto (Obligatorio)

**CrimeTrack Analytics Corp** es una empresa tecnológica que desarrolla y comercializa un
**Sistema de Seguimiento, Gestión y Análisis de Crímenes** para clientes **B2G**:
ministerios de seguridad, instituciones policiales, departamentos de investigación criminal
y organismos gubernamentales.

El enfoque del proyecto es **empresarial B2G**, no solamente operativo policial interno. Por
lo tanto, las decisiones de producto, arquitectura, seguridad y analítica deben servir tanto
a la **operación criminalística** como a la **estrategia comercial de la empresa**.

### Objetivos Estratégicos Obligatorios (INMUTABLES)

Estos cuatro objetivos NO pueden modificarse, reordenarse, sustituirse ni reinterpretarse.
Toda funcionalidad debe poder enlazarse a al menos uno de ellos.

- **OE1 — Penetración de Mercado Digital y Adquisición Automatizada de Clientes (Growth Hacking B2G).**
- **OE2 — Escalabilidad Comercial Exponencial a través de Plataformas de Ecosistemas, Marketplaces y APIs.**
- **OE3 — Expansión Continua Basada en Infraestructura en la Nube de Alta Disponibilidad.**
- **OE4 — Inteligencia de Negocio Centralizada para la Ventaja Competitiva Global.**

## Core Principles

### I. Trazabilidad Estratégica Total (NO NEGOCIABLE)

Ninguna funcionalidad, historia de usuario, requisito o línea de código existe de forma
aislada. Todo artefacto debe trazar una cadena verificable:
**Objetivo Estratégico → Objetivo Táctico → Objetivo Operativo → Departamento → Paquete UML →
Caso de Uso → Historia de Usuario → Requisito (FR/NFR) → Criterio de Aceptación.**
Si un elemento no puede enlazarse a un objetivo estratégico (OE1–OE4), no se especifica ni
se implementa.

### II. Enfoque Empresarial B2G por Diseño

Cada decisión se evalúa desde la doble perspectiva: valor para el cliente gubernamental
(seguridad, legalidad, cadena de custodia) y valor para el negocio de la empresa
(adquisición, escalabilidad, ecosistema de APIs, inteligencia de negocio). No se aceptan
funcionalidades puramente operativas que ignoren la dimensión comercial B2G, ni iniciativas
comerciales que comprometan la integridad criminalística o legal.

### III. Especificación Antes que Código (Spec-Driven, NO NEGOCIABLE)

No se programa nada que no esté previamente especificado y documentado. El orden es:
constitución → especificación → plan → tareas → implementación. Cada módulo se documenta
**antes** de implementarse. Cambios de alcance requieren actualizar primero la especificación.

### IV. Seguridad, Legalidad y Cadena de Custodia como Requisito Base

Al tratarse de datos criminales sensibles para organismos gubernamentales, la seguridad, la
auditoría, la trazabilidad y la cadena de custodia no son características opcionales: son
precondiciones de cualquier funcionalidad. Ningún dato delictivo se crea, modifica, consulta
o elimina sin registro auditable y atribuible a un usuario autenticado.

### V. Modularidad por Paquetes UML y Separación por Niveles Empresariales

El sistema se organiza en paquetes UML cohesivos y débilmente acoplados, alineados con los
niveles empresariales (estratégico, táctico, operativo) y con los departamentos. Cada paquete
tiene una responsabilidad clara, contratos explícitos y puede evolucionar de forma
independiente sin romper la trazabilidad de requisitos.

### VI. Verificabilidad y Demostrabilidad

Todo requisito debe ser verificable y todo caso de uso debe tener criterios de aceptación
medibles. Cada funcionalidad implementada debe poder demostrarse en video acompañada de su
caso de uso documentado. Lo que no se puede verificar ni demostrar, no se considera terminado.

## Enfoque Empresarial B2G

El producto se gobierna como una **plataforma empresarial vendible a gobiernos**, no como una
herramienta interna. En consecuencia:

- **Cliente objetivo:** ministerios de seguridad, instituciones policiales, departamentos de
  investigación criminal y organismos gubernamentales.
- **Propuesta de valor doble:** eficacia criminalística (gestión y análisis de crímenes) +
  resultados de negocio (adquisición automatizada, escalabilidad por ecosistemas/APIs, nube de
  alta disponibilidad e inteligencia de negocio centralizada).
- **Multi-tenant y multi-institución:** la arquitectura asume múltiples organismos clientes con
  aislamiento de datos, configuración por tenant y cumplimiento normativo por jurisdicción.
- **Comercialización:** las capacidades deben ser empaquetables, medibles y exponibles vía
  marketplaces y APIs (OE2), con telemetría de negocio para inteligencia centralizada (OE4).
- **El alcance B2G es inmutable:** no se reduce a un alcance "policial interno" ni se amplía a
  dominios fuera de seguridad/justicia sin enmienda formal de esta constitución.

## Reglas de Alineación con Niveles Empresariales

Toda iniciativa se clasifica y alinea en tres niveles. La especificación de cualquier módulo
debe declarar explícitamente a qué nivel(es) pertenece.

### Nivel Estratégico

- Define el "para qué" comercial e institucional. Se rige por OE1–OE4 (inmutables).
- Responsable de la dirección de producto, expansión de mercado y ventaja competitiva.
- Toda decisión táctica y operativa debe poder justificarse contra uno o más OE.

### Nivel Táctico

- Traduce los objetivos estratégicos en objetivos tácticos por departamento y por capacidad.
- Define metas medibles de mediano plazo (p. ej., integración de APIs, onboarding de clientes,
  paneles de inteligencia, disponibilidad del servicio).
- Cada objetivo táctico debe enlazar "hacia arriba" con un OE y "hacia abajo" con objetivos
  operativos concretos.

### Nivel Operativo

- Define el "cómo" diario: casos de uso, historias de usuario, requisitos funcionales y no
  funcionales, criterios de aceptación.
- Cada objetivo operativo debe enlazar con un objetivo táctico y, por transitividad, con un OE.
- Es el nivel donde se ejecuta, verifica y demuestra la funcionalidad.

## Relación de Trazabilidad Obligatoria

Se establece una cadena de trazabilidad **bidireccional y obligatoria**. Ningún eslabón puede
quedar huérfano.

```
Objetivo Estratégico (OE1–OE4)
  └─ Objetivo Táctico
       └─ Objetivo Operativo
            └─ Departamento Empresarial
                 └─ Paquete UML
                      └─ Caso de Uso
                           └─ Historia de Usuario
                                └─ Requisito Funcional (FR) / No Funcional (NFR)
                                     └─ Criterio de Aceptación
```

Reglas:

- **Cobertura ascendente:** todo Criterio de Aceptación remonta hasta un OE.
- **Cobertura descendente:** todo OE debe materializarse en al menos un objetivo táctico,
  operativo, paquete UML y caso de uso.
- **Departamentos:** cada caso de uso pertenece a un departamento empresarial responsable
  (p. ej., Comercial/Growth, Plataforma/Ingeniería, Operaciones/Cloud, Inteligencia de Negocio,
  Investigación Criminal, Seguridad y Cumplimiento).
- **Sin huérfanos:** una funcionalidad sin enlace estratégico, táctico u operativo se rechaza
  en revisión.
- La matriz de trazabilidad se mantiene actualizada como parte de la documentación del módulo.

## Reglas de Seguridad

- **Autenticación:** acceso solo mediante identidades autenticadas. Credenciales almacenadas con
  hashing fuerte; nunca en texto plano. Tokens/sesiones firmados con claves de longitud segura.
- **Roles y permisos (RBAC):** control de acceso basado en roles con privilegio mínimo. Cada
  acción sensible exige un permiso explícito; los permisos se verifican en el backend, no solo
  en la interfaz.
- **Sesiones:** sesiones con expiración, renovación controlada y cierre/revocación. Estado de
  sesión verificable y revocable por administración.
- **MFA (si aplica):** autenticación multifactor obligatoria para roles administrativos y
  operaciones de alto impacto (gestión de usuarios, exportaciones masivas, configuración del
  sistema, restauración de respaldos). Para clientes B2G que lo exijan, MFA es obligatorio.
- **Auditoría:** registro de auditoría inmutable de eventos relevantes (login/logout, accesos,
  cambios de datos, exportaciones, cambios de configuración y permisos), con usuario, fecha/hora,
  origen y resultado.
- **Trazabilidad:** toda operación sobre datos delictivos es atribuible a un usuario y momento
  específicos, y reconstruible a partir de los registros.
- **Cadena de custodia:** las evidencias y registros criminalísticos mantienen un historial
  íntegro e inalterable de creación, acceso, modificación, transferencia y custodia, preservando
  validez legal. Cualquier alteración queda registrada y nunca sobrescribe el historial previo.

## Reglas de Arquitectura

- **Modularidad por paquetes UML:** el sistema se compone de paquetes UML cohesivos con contratos
  explícitos y bajo acoplamiento.
- **Separación por niveles empresariales:** la estructura refleja los niveles estratégico,
  táctico y operativo, evitando mezclar responsabilidades de distinto nivel en un mismo módulo.
- **Trazabilidad de requisitos:** la arquitectura preserva el enlace requisito ↔ componente ↔
  caso de uso; cada componente declara qué requisitos satisface.
- **Integración con APIs:** capacidades expuestas mediante APIs versionadas, documentadas y
  seguras, habilitando ecosistemas y marketplaces (OE2). Contratos estables y retrocompatibles.
- **Cloud de alta disponibilidad:** despliegue sobre infraestructura en la nube con
  redundancia, escalabilidad y recuperación ante desastres (OE3); diseño tolerante a fallos.
- **Gobierno de datos:** clasificación, calidad, retención, privacidad y soberanía de datos por
  jurisdicción; aislamiento por tenant; políticas de acceso y ciclo de vida del dato.
- **Analítica criminal:** capa analítica para análisis y correlación de crímenes que alimenta la
  inteligencia de negocio centralizada (OE4), sin comprometer privacidad ni cadena de custodia.

## Reglas de Documentación

- **Casos de uso:** todo caso de uso debe incluir, como mínimo: **actor**, **objetivo**,
  **precondición**, **flujo principal**, **flujo alternativo** y **criterio de aceptación**.
- **Historias de usuario:** toda historia de usuario debe estar asociada a un **caso de uso** y a
  un **objetivo operativo** (y, por transitividad, a un OE).
- **Sin funcionalidad huérfana:** no debe existir funcionalidad sin relación explícita con
  objetivos estratégicos, tácticos u operativos.
- **Documentación previa:** cada módulo se documenta antes de implementarse, incluyendo su
  ubicación en la matriz de trazabilidad.
- **Idioma y claridad:** la documentación es clara, legible y consistente; los diagramas son
  legibles y proporcionados (ver Reglas de Implementación).

## Reglas de Implementación

- **No programar fuera de especificación:** no se implementan funcionalidades que no estén
  previamente especificadas y aprobadas.
- **No modificar el alcance empresarial B2G:** el alcance B2G es inmutable salvo enmienda formal.
- **No cambiar los objetivos estratégicos:** OE1, OE2, OE3 y OE4 son inmutables.
- **Calidad visual de gráficos:** no se crean gráficos miniatura, alargados, deformados ni
  ilegibles; toda visualización debe ser clara, proporcionada y legible.
- **Documentar antes de implementar:** cada módulo debe estar documentado antes de escribir su
  código.
- **Cambios de alcance:** primero se actualiza la especificación/constitución; luego se
  implementa.

## Reglas de Validación

- **Checklist por módulo:** cada módulo debe contar con un checklist de validación verificable.
- **Requisitos verificables:** cada requisito (FR/NFR) debe ser verificable de forma objetiva.
- **Criterios de aceptación por caso de uso:** cada caso de uso debe tener criterios de
  aceptación explícitos y comprobables.
- **Demostrabilidad en video:** cada funcionalidad implementada debe poder mostrarse en video
  acompañada de su caso de uso documentado.
- **Definición de "Hecho":** un elemento solo se considera terminado cuando cumple su checklist,
  satisface sus criterios de aceptación, conserva trazabilidad y es demostrable.

## Governance

- Esta constitución **prevalece** sobre cualquier otra práctica, preferencia o decisión ad hoc
  del proyecto. En caso de conflicto, manda la constitución.
- Los **cuatro objetivos estratégicos (OE1–OE4)** y el **alcance empresarial B2G** son
  **inmutables**: no pueden alterarse mediante enmienda ordinaria.
- **Enmiendas:** cualquier cambio (excepto OE1–OE4 y el alcance B2G) requiere: (1) justificación
  documentada, (2) actualización de las especificaciones y matriz de trazabilidad afectadas,
  (3) aprobación explícita y (4) registro de versión.
- **Cumplimiento:** toda especificación, plan, conjunto de tareas y revisión de código debe
  verificar el cumplimiento de esta constitución antes de avanzar. Las desviaciones deben
  justificarse y documentarse, o ser rechazadas.
- **Versionado semántico de la constitución:** MAJOR para cambios incompatibles de gobierno o
  principios; MINOR para nuevos principios/secciones o ampliaciones materiales; PATCH para
  aclaraciones y correcciones no semánticas.

**Version**: 1.0.0 | **Ratified**: 2026-06-20 | **Last Amended**: 2026-06-20
