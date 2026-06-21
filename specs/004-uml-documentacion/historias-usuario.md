# Historias de Usuario — CrimeTrack Analytics Corp

> 105 historias (10 estratégicas, 16 tácticas, 79 operativas; incluye **16 nuevas de auditoría**
> HU-O-61…HU-O-76 y **3 de operaciones de patrulla** HU-O-77, HU-O-78 y HU-O-78b). Formato:
> **HU-[Nivel]-[Número]** — "Como [actor], quiero [necesidad], para [beneficio]".
> Cada historia incluye: Código, Rol, Necesidad, Beneficio, Caso de uso, Paquete UML, Objetivo,
> Criterios de aceptación y Prioridad. Subordinado a `000-sistema-general/` y a la constitución.

Convención de prioridad: **Alta** (crítica/seguridad/núcleo/demo), **Media** (negocio/analítica),
**Baja** (apoyo). Toda HU traza a un CU y a un objetivo (sin huérfanos, RD-02/RD-03).

---

## Historias Estratégicas (HU-E)

| Código | Rol | Quiero (necesidad) | Para (beneficio) | CU | Paquete | Objetivo | Prioridad |
|---|---|---|---|---|---|---|---|
| HU-E-01 | Ejecutivo Corporativo | consultar el Balanced Scorecard | tomar decisiones con visión integral | CU-E01 | P12 | OE4 | Alta |
| HU-E-02 | Ejecutivo/Gerente Comercial | analizar la penetración de mercado B2G | priorizar regiones y segmentos | CU-E02 | P12/P09 | OE1 | Alta |
| HU-E-03 | Ejecutivo Corporativo | analizar la rentabilidad ARR/MRR | evaluar la salud financiera | CU-E03 | P12 | OE4 | Alta |
| HU-E-04 | Ejecutivo Corporativo | definir metas y OKR | alinear la organización con OE1–OE4 | CU-E04 | P12 | OE4 | Media |
| HU-E-05 | Ejecutivo/Analista BI | analizar la ventaja competitiva | sostener la diferenciación global | CU-E05 | P12 | OE4 | Media |
| HU-E-06 | Ejecutivo/SRE | evaluar disponibilidad cloud y SLA | garantizar continuidad y confianza | CU-E06 | P11 | OE3 | Alta |
| HU-E-07 | Ejecutivo/Gerente Comercial | revisar crecimiento por marketplace y APIs | impulsar el ecosistema | CU-E07 | P10/P09 | OE2 | Media |
| HU-E-08 | Ejecutivo Corporativo | generar el reporte ejecutivo | comunicar resultados a la junta | CU-E08 | P08/P12 | OE4 | Media |
| HU-E-09 | Ejecutivo/Gerente Comercial | analizar la expansión geográfica | planear el crecimiento institucional | CU-E09 | P12/P09 | OE1 | Media |
| HU-E-10 | Ejecutivo Corporativo | aprobar el roadmap estratégico | dirigir la evolución del producto | CU-E10 | P12 | OE4 | Alta |

**Criterios de aceptación (HU-E):**
- HU-E-01 — Dado MFA válido, Cuando abro el BSC, Entonces veo 4 perspectivas con datos vigentes y legibles.
- HU-E-02 — Dado un periodo, Cuando filtro por región/segmento, Entonces obtengo penetración (KPI-03).
- HU-E-03 — Dado un periodo, Cuando consulto ARR/MRR, Entonces el valor es correcto y exportable (KPI-10).
- HU-E-04 — Dado un OKR, Cuando lo registro, Entonces queda ligado a KPIs y a un OE sin contradecir OE1–OE4.
- HU-E-05 — Dadas dimensiones, Cuando ejecuto el análisis, Entonces obtengo un benchmark legible (KPI-11).
- HU-E-06 — Dado un periodo, Cuando reviso SLA, Entonces veo uptime y cumplimiento (KPI-07/08).
- HU-E-07 — Dado un periodo, Cuando reviso el ecosistema, Entonces veo KPI-04/05/06.
- HU-E-08 — Dado un alcance, Cuando genero el reporte, Entonces obtengo un documento consolidado y legible.
- HU-E-09 — Dado un mapa, Cuando filtro por jurisdicción, Entonces veo cobertura y potencial.
- HU-E-10 — Dado el roadmap, Cuando lo apruebo, Entonces queda versionado y auditado.

---

## Historias Tácticas (HU-T)

| Código | Rol | Quiero (necesidad) | Para (beneficio) | CU | Paquete | Objetivo | Prioridad |
|---|---|---|---|---|---|---|---|
| HU-T-01 | Especialista Growth | gestionar campañas Growth B2G | adquirir clientes de forma automatizada | CU-T01 | P09 | OE1 | Alta |
| HU-T-02 | Gerente Comercial | administrar el pipeline institucional | convertir oportunidades | CU-T02 | P09 | OE1 | Alta |
| HU-T-03 | Gerente Comercial | gestionar demos y pilotos | acelerar la decisión de compra | CU-T03 | P09 | OE1 | Media |
| HU-T-04 | Gerente/Legal | gestionar licitaciones y RFP | ganar contratos públicos | CU-T04 | P09 | OE1 | Media |
| HU-T-05 | SRE/Plataforma | configurar el catálogo de APIs | habilitar el ecosistema | CU-T05 | P10 | OE2 | Alta |
| HU-T-06 | SRE/Integrador | gestionar integraciones externas | conectar sistemas de terceros | CU-T06 | P10 | OE2 | Media |
| HU-T-07 | Gerente Comercial | gestionar marketplace y planes SaaS | escalar comercialmente | CU-T07 | P10 | OE2 | Media |
| HU-T-08 | Administrador | configurar roles y permisos institucionales | aplicar privilegio mínimo | CU-T08 | P02/P01 | OT5 | Alta |
| HU-T-09 | SRE | gestionar SLA y monitoreo cloud | cumplir compromisos de servicio | CU-T09 | P11 | OE3 | Alta |
| HU-T-10 | Analista BI | gestionar el data warehouse | centralizar datos confiables | CU-T10 | P12 | OE4 | Alta |
| HU-T-11 | Analista BI | configurar KPIs y tableros | medir el negocio | CU-T11 | P12/P04 | OE4 | Media |
| HU-T-12 | Auditor | gestionar auditoría y cumplimiento | asegurar conformidad legal | CU-T12 | P03 | OT5 | Alta |
| HU-T-13 | Gerente Comercial | gestionar paquetes por cliente | adaptar la oferta | CU-T13 | P09 | OE1/OE2 | Media |
| HU-T-14 | Gerente/Legal | administrar contratos y licencias | formalizar la relación B2G | CU-T14 | P09/P02 | OE1 | Alta |
| HU-T-15 | Customer Success | gestionar onboarding y capacitación | acelerar la adopción | CU-T15 | P09 | OE1 | Media |
| HU-T-16 | Customer Success | gestionar soporte y success | retener y expandir cuentas | CU-T16 | P09 | OE1 | Media |

**Criterios de aceptación (HU-T):**
- HU-T-01 — Dado un segmento, Cuando creo una campaña, Entonces queda medible por KPI-02.
- HU-T-02 — Dado el pipeline, Cuando muevo una oportunidad, Entonces se actualiza el avance.
- HU-T-03 — Dada una oportunidad, Cuando agendo un piloto, Entonces queda registrado con resultados.
- HU-T-04 — Dado un RFP, Cuando registro avances, Entonces se conserva el historial y documentos.
- HU-T-05 — Dada una API, Cuando la publico, Entonces queda versionada y documentada.
- HU-T-06 — Dada una integración, Cuando la configuro, Entonces se valida conectividad y se audita.
- HU-T-07 — Dado un plan, Cuando lo publico, Entonces aparece en el marketplace.
- HU-T-08 — Dado un rol, Cuando lo configuro, Entonces aplica privilegio mínimo y queda auditado.
- HU-T-09 — Dado un umbral, Cuando se incumple, Entonces se genera alerta (KPI-08).
- HU-T-10 — Dada una fuente, Cuando la integro, Entonces el DWH tiene calidad y linaje (KPI-12).
- HU-T-11 — Dado un KPI, Cuando lo configuro, Entonces aparece en su tablero, legible.
- HU-T-12 — Dado un periodo, Cuando audito, Entonces obtengo evidencia de cumplimiento (KPI-18/19).
- HU-T-13 — Dado un cliente, Cuando armo su paquete, Entonces sus capacidades reflejan el contrato.
- HU-T-14 — Dado un contrato, Cuando lo activo, Entonces habilita capacidades y se audita.
- HU-T-15 — Dado un cliente nuevo, Cuando completo onboarding, Entonces queda activo y capacitado.
- HU-T-16 — Dado un caso, Cuando lo resuelvo, Entonces se cierra con métrica de satisfacción.

---

## Historias Operativas (HU-O)

> Una historia por caso de uso operativo (HU-O-01 ↔ CU-O01, …, HU-O-60 ↔ CU-O60). El criterio de
> aceptación detallado en formato Dado/Cuando/Entonces de cada historia coincide con el de su caso
> de uso en `casos-uso.md`; aquí se incluye su forma resumida.

| Código | Rol | Quiero (necesidad) | Para (beneficio) | CU | Paquete | Objetivo | Prioridad |
|---|---|---|---|---|---|---|---|
| HU-O-01 | Usuario Institucional | iniciar sesión | acceder de forma segura | CU-O01 | P01 | OT5 | Alta |
| HU-O-02 | Usuario/Administrador | gestionar MFA | proteger accesos críticos | CU-O02 | P01 | OT5 | Alta |
| HU-O-03 | Usuario Institucional | recuperar mi contraseña | recobrar acceso sin riesgo | CU-O03 | P01 | OT5 | Media |
| HU-O-04 | Administrador | gestionar sesiones activas | revocar accesos indebidos | CU-O04 | P01 | OT5 | Media |
| HU-O-05 | Usuario Institucional | que se validen mis permisos | operar solo lo autorizado | CU-O05 | P01 | OT5 | Alta |
| HU-O-06 | Administrador | registrar una institución cliente | aprovisionar un tenant | CU-O06 | P02 | OE1 | Alta |
| HU-O-07 | Administrador | gestionar usuarios y roles | controlar el acceso | CU-O07 | P02 | OT5 | Alta |
| HU-O-08 | Administrador | configurar parámetros y catálogos | adaptar el sistema | CU-O08 | P02 | OT5 | Media |
| HU-O-09 | Administrador/Comercial | gestionar licencias y planes | habilitar capacidades | CU-O09 | P02 | OE1/OE2 | Media |
| HU-O-10 | Comercial/Legal | registrar contrato y SLA | formalizar el servicio | CU-O10 | P02 | OE1/OE3 | Alta |
| HU-O-11 | Sistema/Auditor | registrar bitácora de acceso | trazar la actividad | CU-O11 | P03 | OT5 | Alta |
| HU-O-12 | Auditor | consultar trazabilidad | reconstruir hechos | CU-O12 | P03 | OT5 | Alta |
| HU-O-13 | Auditor | exportar logs de auditoría | aportar evidencia | CU-O13 | P03 | OT5 | Media |
| HU-O-14 | Auditor/Sistema | generar alerta de manipulación | proteger la integridad | CU-O14 | P03 | OT5 | Alta |
| HU-O-15 | Auditor/Custodio | validar la cadena de custodia | preservar validez legal | CU-O15 | P03 | OT5 | Alta |
| HU-O-16 | Analista Criminal | visualizar el mapa de calor | focalizar la prevención | CU-O16 | P04 | OE4 | Alta |
| HU-O-17 | Analista Criminal | consultar indicadores criminales | entender la situación | CU-O17 | P04 | OE4 | Media |
| HU-O-18 | Analista Criminal | ejecutar filtros analíticos | segmentar la información | CU-O18 | P04 | OE4 | Media |
| HU-O-19 | Analista Criminal | consultar tendencias delictivas | anticipar patrones | CU-O19 | P04 | OE4 | Media |
| HU-O-20 | Analista Criminal | generar predicción criminal | prevenir delitos | CU-O20 | P04 | OE4 | Media |
| HU-O-21 | Investigador | crear un expediente | iniciar la investigación | CU-O21 | P05 | OE4 | Alta |
| HU-O-22 | Administrador/Investigador | asignar investigador | responsabilizar el caso | CU-O22 | P05 | OE4 | Media |
| HU-O-23 | Investigador | actualizar el estado | reflejar el avance | CU-O23 | P05 | OE4 | Media |
| HU-O-24 | Investigador | vincular delitos/evidencias/involucrados | construir el caso | CU-O24 | P05 | OE4 | Alta |
| HU-O-25 | Investigador/Administrador | cerrar un expediente | concluir el caso | CU-O25 | P05 | OE4 | Alta |
| HU-O-26 | Custodio | registrar una evidencia | incorporarla al caso | CU-O26 | P06 | OE4 | Alta |
| HU-O-27 | Custodio | cargar el archivo de evidencia | almacenar el material | CU-O27 | P06 | OE4 | Alta |
| HU-O-28 | Sistema | calcular el hash | garantizar integridad | CU-O28 | P06 | OE4 | Alta |
| HU-O-29 | Custodio | gestionar la custodia | mantener trazabilidad legal | CU-O29 | P06 | OE4 | Alta |
| HU-O-30 | Investigador/Auditor | consultar evidencia autorizada | revisar el material | CU-O30 | P06 | OE4 | Media |
| HU-O-31 | Investigador | registrar una víctima | documentar al afectado | CU-O31 | P07 | OE4 | Alta |
| HU-O-32 | Investigador | registrar un sospechoso | seguir la línea investigativa | CU-O32 | P07 | OE4 | Alta |
| HU-O-33 | Investigador | registrar un testigo | recabar testimonios | CU-O33 | P07 | OE4 | Media |
| HU-O-34 | Investigador | vincular involucrado a expediente | relacionar el caso | CU-O34 | P07 | OE4 | Media |
| HU-O-35 | Investigador/Analista | consultar historial de involucrado | identificar antecedentes | CU-O35 | P07 | OE4 | Media |
| HU-O-36 | Investigador/Usuario | generar un reporte operativo | comunicar resultados | CU-O36 | P08 | OE4 | Alta |
| HU-O-37 | Investigador/Usuario | exportar a PDF/Excel | compartir formalmente | CU-O37 | P08 | OE4 | Alta |
| HU-O-38 | Administrador/Usuario | programar reportes | automatizar la entrega | CU-O38 | P08 | OE4 | Baja |
| HU-O-39 | Usuario Institucional | emitir un informe institucional | cumplir requerimientos | CU-O39 | P08 | OE4 | Media |
| HU-O-40 | Usuario Institucional | enviar reporte autorizado | distribuir con control | CU-O40 | P08 | OE4 | Media |
| HU-O-41 | Especialista Growth/Comercial | registrar un lead B2G | iniciar la captación | CU-O41 | P09 | OE1 | Alta |
| HU-O-42 | Gerente Comercial | calificar la oportunidad | priorizar esfuerzos | CU-O42 | P09 | OE1 | Media |
| HU-O-43 | Gerente Comercial | programar una demo | impulsar la venta | CU-O43 | P09 | OE1 | Media |
| HU-O-44 | Gerente/Legal | registrar avance de RFP | seguir la licitación | CU-O44 | P09 | OE1 | Media |
| HU-O-45 | Gerente Comercial | generar una propuesta B2G | cerrar el contrato | CU-O45 | P09 | OE1 | Alta |
| HU-O-46 | SRE/Integrador | registrar una API key | habilitar integración segura | CU-O46 | P10 | OE2 | Alta |
| HU-O-47 | Integrador/SRE | consultar documentación API | integrar correctamente | CU-O47 | P10 | OE2 | Media |
| HU-O-48 | SRE/Integrador | configurar un webhook | recibir eventos | CU-O48 | P10 | OE2 | Media |
| HU-O-49 | Sistema | registrar el consumo de API | medir el uso | CU-O49 | P10 | OE2 | Media |
| HU-O-50 | SRE | gestionar conectores externos | mantener integraciones | CU-O50 | P10 | OE2 | Media |
| HU-O-51 | SRE | monitorear el uptime | asegurar disponibilidad | CU-O51 | P11 | OE3 | Alta |
| HU-O-52 | SRE/Sistema | ejecutar backup programado | proteger los datos | CU-O52 | P11 | OE3 | Alta |
| HU-O-53 | SRE/Sistema | activar escalamiento automático | sostener la demanda | CU-O53 | P11 | OE3 | Media |
| HU-O-54 | SRE | registrar incidentes SLA | gestionar el cumplimiento | CU-O54 | P11 | OE3 | Media |
| HU-O-55 | SRE | ejecutar recuperación ante desastres | restaurar el servicio | CU-O55 | P11 | OE3 | Alta |
| HU-O-56 | Analista BI | consolidar datos | centralizar la información | CU-O56 | P12 | OE4 | Alta |
| HU-O-57 | Analista BI/Sistema | calcular KPIs corporativos | medir el desempeño | CU-O57 | P12 | OE4 | Media |
| HU-O-58 | Analista BI | generar benchmark | comparar el rendimiento | CU-O58 | P12 | OE4 | Media |
| HU-O-59 | Ejecutivo/Analista BI | exportar tablero ejecutivo | compartir con la dirección | CU-O59 | P12 | OE4 | Baja |
| HU-O-60 | Analista BI | ejecutar el forecast B2G | planear la demanda | CU-O60 | P12 | OE4 | Media |

**Criterios de aceptación (HU-O) — forma resumida (detalle Dado/Cuando/Entonces en `casos-uso.md`):**
- HU-O-01..05 (P01): acceso seguro con MFA, recuperación verificada, revocación de sesiones y denegación auditada por permiso.
- HU-O-06..10 (P02): alta de institución con aislamiento, gestión de usuarios/roles auditada, parámetros válidos, licencias y contrato/SLA vigentes.
- HU-O-11..15 (P03): registros inmutables, traza reconstruible, exportación auditada, alerta de manipulación y validación de custodia.
- HU-O-16..20 (P04): visualizaciones legibles (RI-04), indicadores y tendencias correctos, predicción con nivel de confianza.
- HU-O-21..25 (P05): expediente con folio único, asignación, estados válidos, vínculos trazables y cierre solo si completo (RN-09).
- HU-O-26..30 (P06): evidencia con metadatos, archivo cifrado, hash verificable, custodia sin pérdida de historial y acceso autorizado auditado.
- HU-O-31..35 (P07): involucrados con protección de datos, vinculados a expedientes y con historial consultable.
- HU-O-36..40 (P08): reportes correctos y legibles, exportación PDF/Excel auditada, programación, informe oficial y envío solo a autorizados.
- HU-O-41..45 (P09): lead registrado, oportunidad calificada al pipeline, demo agendada, avance de RFP con historial y propuesta legible.
- HU-O-46..50 (P10): API key con scopes, documentación versionada, webhook validado, consumo contabilizado y conectores monitoreados.
- HU-O-51..55 (P11): uptime medido, backup ejecutado y registrado, autoescalado, incidentes que afectan KPI-08 y DR dentro de RTO/RPO.
- HU-O-56..60 (P12): consolidación íntegra, KPIs correctos, benchmark legible, exportación proporcionada (RI-04) y forecast con su precisión.

---

## Historias Operativas — NIVEL AUDITORÍA (NUEVAS, HU-O-61…HU-O-76)

> **Implementado adicional.** Una historia por cada caso de uso nuevo de auditoría (HU-O-61 ↔
> CU-O61, …, HU-O-76 ↔ CU-O76), todas del paquete **P03**. Detalle del criterio Dado/Cuando/Entonces
> en `casos-uso.md`, sección "CASOS DE USO NUEVOS — NIVEL AUDITORÍA (P03)".

| Código | Rol | Quiero (necesidad) | Para (beneficio) | CU | Paquete | Objetivo | Prioridad |
|---|---|---|---|---|---|---|---|
| HU-O-61 | Sistema/Auditor | registrar toda operación CRUD con valores antes/después | reconstruir cualquier cambio | CU-O61 | P03 | OT5 | Alta |
| HU-O-62 | Sistema/Auditor | auditar autenticación y sesiones (inicio, fin, duración, dispositivo) | saber quién accedió, cómo y por cuánto tiempo | CU-O62 | P03 | OT5 | Alta |
| HU-O-63 | Sistema/Auditor | auditar roles, permisos y privilegios | controlar la autorización y la elevación de privilegios | CU-O63 | P03 | OT5 | Alta |
| HU-O-64 | Sistema/Auditor | auditar el acceso a información sensible por modo | saber quién vio/descargó/exportó datos reservados | CU-O64 | P03 | OT5 | Alta |
| HU-O-65 | Sistema/Auditor | auditar el ciclo de vida de los expedientes | reconstruir la historia completa del caso | CU-O65 | P03 | OE4 | Alta |
| HU-O-66 | Sistema/Custodio | auditar evidencias y cadena de custodia con hash | preservar la validez legal de la evidencia | CU-O66 | P03 | OE4 | Alta |
| HU-O-67 | Sistema/Auditor | auditar a los involucrados y sus datos protegidos | proteger la información personal y su trazabilidad | CU-O67 | P03 | OE4 | Media |
| HU-O-68 | Sistema/Auditor | auditar reportes, archivos y exportaciones | controlar la salida de información | CU-O68 | P03 | OE4 | Alta |
| HU-O-69 | Sistema/Auditor | auditar la administración y configuración | rastrear cambios críticos del sistema | CU-O69 | P03 | OT5 | Alta |
| HU-O-70 | Sistema/Auditor | auditar APIs e integraciones sin exponer secretos | controlar el consumo y los accesos externos | CU-O70 | P03 | OE2 | Media |
| HU-O-71 | Sistema/SRE | auditar la infraestructura cloud y la continuidad | trazar backups, incidentes y recuperaciones | CU-O71 | P03 | OE3 | Media |
| HU-O-72 | Sistema/Analista BI | auditar analítica, BI e IA | trazar consultas, modelos y datasets | CU-O72 | P03 | OE4 | Media |
| HU-O-73 | Auditor/Compliance | consultar el tablero central de auditoría | buscar y reconstruir cualquier actividad | CU-O73 | P03 | OT5 | Alta |
| HU-O-74 | Auditor/Compliance | generar reportes de auditoría y cumplimiento | demostrar conformidad legal | CU-O74 | P03 | OT5 | Alta |
| HU-O-75 | Sistema/Auditor | verificar la integridad de la auditoría | detectar cualquier manipulación de logs | CU-O75 | P03 | OT5 | Alta |
| HU-O-76 | Auditor/Compliance | gestionar retención y archivado de auditoría | conservar históricos sin perder integridad | CU-O76 | P03 | OT5 | Media |

**Criterios de aceptación (HU-O NIVEL AUDITORÍA) — forma resumida (detalle en `casos-uso.md`):**
- HU-O-61 — Dado un INSERT/UPDATE/DELETE, Cuando ocurre, Entonces se registra evento inmutable con usuario, rol, registro y valores anterior/nuevo.
- HU-O-62 — Dado un inicio y cierre de sesión, Cuando ocurren, Entonces se registran inicio, última actividad, cierre, duración, IP, dispositivo y navegador.
- HU-O-63 — Dada una asignación de rol o acceso denegado, Cuando ocurre, Entonces queda registrado el responsable, el permiso y el resultado.
- HU-O-64 — Dado un acceso a información sensible, Cuando se realiza, Entonces se registra quién, qué registro y el modo (consulta/descarga/exportación…).
- HU-O-65 — Dado un cambio de estado/reasignación de expediente, Cuando ocurre, Entonces el historial registra antes/después, usuario y motivo.
- HU-O-66 — Dada una transferencia de custodia, Cuando se registra, Entonces conserva custodio anterior/nuevo, fecha, motivo y hash verificable; una ruptura genera alerta.
- HU-O-67 — Dada una actualización de un involucrado, Cuando ocurre, Entonces se registra responsable, motivo y valores anterior/nuevo enmascarados.
- HU-O-68 — Dada una exportación, Cuando se realiza, Entonces se registra solicitante, formato, parámetros, destinatarios y motivo si es sensible.
- HU-O-69 — Dado un cambio de parámetro/configuración, Cuando se guarda, Entonces se registra el responsable y los valores anterior/nuevo.
- HU-O-70 — Dada una llamada API, Cuando se procesa, Entonces se registra endpoint, método, código y latencia sin almacenar token/API key completos.
- HU-O-71 — Dada una ejecución de backup o incidente SLA, Cuando ocurre, Entonces se registra resultado, tiempos y responsable.
- HU-O-72 — Dada una ejecución de modelo predictivo, Cuando se realiza, Entonces se registra modelo, versión, parámetros, dataset y resultado.
- HU-O-73 — Dado un auditor, Cuando filtra por usuario/rol/sesión/módulo/CU/entidad/fecha/IP, Entonces obtiene la traza completa, paginada y legible.
- HU-O-74 — Dado un periodo, Cuando genera un reporte de cumplimiento, Entonces obtiene un documento legible y la exportación queda registrada.
- HU-O-75 — Dada una manipulación de un log, Cuando se ejecuta la verificación, Entonces se detecta la ruptura de la cadena y se notifica.
- HU-O-76 — Dada una política de retención, Cuando vence un rango, Entonces los logs se archivan sin perder integridad y el archivado queda autorizado y registrado.

---

## Historias Operativas — OPERACIONES DE PATRULLA (NUEVAS, HU-O-77…HU-O-78)

> **Implementado adicional.** Extienden P05 hacia la coordinación de patrullas y despacho
> (HU-O-77 ↔ CU-O77, HU-O-78 ↔ CU-O78). Regla principal: **el Comisario despacha y supervisa el
> cierre; el Oficial registra, recibe, atiende y reporta** (el Oficial no despacha). Detalle del
> criterio en `casos-uso.md`, sección "CASOS DE USO NUEVOS — OPERACIONES DE PATRULLA (P05)".

| Código | Rol | Quiero (necesidad) | Para (beneficio) | CU | Paquete | Objetivo | Prioridad |
|---|---|---|---|---|---|---|---|
| HU-O-77 | Comisario | asignar oficiales a una patrulla y turno | organizar la cobertura operativa del territorio | CU-O77 | P05 | OE4 | Alta |
| HU-O-78 | Comisario | evaluar, definir prioridad, despachar la patrulla y aprobar el cierre del incidente | atender los incidentes con la unidad adecuada y supervisar su resolución | CU-O78 | P05 | OE4 | Alta |
| HU-O-78b | Oficial | registrar el incidente, aceptar el despacho, atenderlo, solicitar apoyo y generar el parte | resolver el incidente en terreno y dejar constancia para revisión del Comisario | CU-O78 | P05 | OE4 | Alta |

**Criterios de aceptación (HU-O OPERACIONES DE PATRULLA):**
- HU-O-77 — Dada una patrulla y oficiales disponibles, Cuando el Comisario los asigna, Entonces la patrulla queda conformada con su turno y responsable, sin solapes, y el cambio queda auditado.
- HU-O-78 — Dado un incidente reportado y una patrulla disponible, Cuando el Comisario define prioridad y la despacha, Entonces la unidad queda vinculada al incidente ("Despachado") y, tras la atención del Oficial, el Comisario puede aprobar el cierre o devolver el caso, todo auditado.
- HU-O-78b — Dado un incidente despachado a su patrulla, Cuando el Oficial lo acepta, atiende y finaliza con el parte, Entonces el incidente queda "Atendido" a la espera de la revisión del Comisario, y cada transición queda auditada.

---

## Resumen de Historias

| Nivel | Rango | Cantidad |
|---|---|---|
| Estratégicas | HU-E-01…HU-E-10 | 10 |
| Tácticas | HU-T-01…HU-T-16 | 16 |
| Operativas | HU-O-01…HU-O-60 | 60 |
| Operativas — NIVEL AUDITORÍA (nuevas) | HU-O-61…HU-O-76 | 16 |
| Operativas — OPERACIONES DE PATRULLA (nuevas) | HU-O-77, HU-O-78, HU-O-78b | 3 |
| **Total** | | **105** |

Ninguna historia queda sin caso de uso ni sin objetivo (RD-02/RD-03). No se detectaron historias
duplicadas; cualquier nueva se marcaría como "Implementado adicional".

