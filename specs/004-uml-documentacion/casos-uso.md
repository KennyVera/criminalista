# Casos de Uso — CrimeTrack Analytics Corp

> 102 casos de uso (10 estratégicos, 16 tácticos, 76 operativos). Cada caso incluye, conforme a la
> constitución (RD-01): **actor, objetivo, precondición, flujo principal, flujo alternativo y
> criterio de aceptación** (Dado/Cuando/Entonces). Los **casos de uso nuevos de auditoría**
> (CU-O61…CU-O76) incluyen además la estructura completa de 18 puntos exigida para P03.
> Subordinado a `000-sistema-general/`.

## Índice

- Estratégicos: CU-E01…CU-E10 (Nivel estratégico).
- Tácticos: CU-T01…CU-T16 (Nivel táctico).
- Operativos: CU-O01…CU-O60 (Nivel operativo, P01–P12).
- **Operativos — NIVEL AUDITORÍA (NUEVOS):** CU-O61…CU-O76 (Nivel operativo, P03). Ver sección
  **"CASOS DE USO NUEVOS — NIVEL AUDITORÍA (P03)"**.

---

# Casos de Uso Estratégicos (CU-E)

### CU-E01 — Consultar tablero Balanced Scorecard empresarial
- **Actor:** A07 Ejecutivo Corporativo. **Paquete:** P12. **OE/OT:** OE4/OT4.
- **Objetivo:** visualizar el cuadro de mando integral con las 4 perspectivas.
- **Precondición:** ejecutivo autenticado con MFA; KPIs y DWH configurados.
- **Flujo principal:** 1) Accede al panel estratégico. 2) Selecciona Balanced Scorecard. 3) El sistema consolida y muestra perspectivas financiera, cliente, procesos y aprendizaje. 4) El ejecutivo analiza indicadores.
- **Flujo alternativo:** datos parciales → se indica cobertura y faltantes.
- **Criterio de aceptación:** Dado un ejecutivo con MFA, Cuando abre el BSC, Entonces visualiza las 4 perspectivas con datos vigentes y legibles.

### CU-E02 — Analizar penetración de mercado B2G
- **Actor:** A07, A08. **Paquete:** P12/P09. **OE/OT:** OE1/OT1.
- **Objetivo:** medir penetración por región y segmento institucional.
- **Precondición:** datos comerciales consolidados (CU-O56).
- **Flujo principal:** 1) Selecciona análisis de mercado. 2) Filtra por región/segmento. 3) El sistema muestra penetración y oportunidades.
- **Flujo alternativo:** segmento sin datos → aviso de cobertura.
- **Criterio de aceptación:** Dado un periodo, Cuando consulta penetración, Entonces obtiene métricas por región/segmento (KPI-03) legibles.

### CU-E03 — Analizar rentabilidad ARR/MRR gubernamental
- **Actor:** A07. **Paquete:** P12. **OE/OT:** OE4/OT4.
- **Objetivo:** evaluar ingreso recurrente anual/mensual.
- **Precondición:** datos de contratos/licencias consolidados.
- **Flujo principal:** 1) Selecciona ARR/MRR. 2) Define periodo. 3) El sistema calcula y muestra ingresos recurrentes.
- **Flujo alternativo:** exportación del análisis (auditada).
- **Criterio de aceptación:** Dado un periodo, Cuando consulta ARR/MRR, Entonces obtiene el ingreso recurrente correcto y exportable (KPI-10).

### CU-E04 — Definir metas y OKR corporativos
- **Actor:** A07. **Paquete:** P12. **OE/OT:** OE4/OT4.
- **Objetivo:** registrar y dar seguimiento a OKR vinculados a KPIs.
- **Precondición:** catálogo de KPIs disponible (CU-T11).
- **Flujo principal:** 1) Crea objetivo. 2) Define resultados clave y KPIs. 3) El sistema valida coherencia con OE1–OE4 y persiste.
- **Flujo alternativo:** OKR que contradice un OE → rechazado (RN-04).
- **Criterio de aceptación:** Dado un OKR nuevo, Cuando lo registra, Entonces queda vinculado a KPIs y a un OE sin contradecir OE1–OE4.

### CU-E05 — Analizar ventaja competitiva global
- **Actor:** A07, A11. **Paquete:** P12. **OE/OT:** OE4/OT4.
- **Objetivo:** comparar desempeño frente a referencias del mercado.
- **Precondición:** datos de benchmark (CU-O58).
- **Flujo principal:** 1) Selecciona análisis competitivo. 2) Elige dimensiones. 3) El sistema muestra benchmark.
- **Flujo alternativo:** falta de datos de referencia → marcado como pendiente.
- **Criterio de aceptación:** Dado un conjunto de dimensiones, Cuando ejecuta el análisis, Entonces obtiene un benchmark legible (KPI-11).

### CU-E06 — Evaluar disponibilidad cloud y SLA
- **Actor:** A07, A10. **Paquete:** P11. **OE/OT:** OE3/OT3.
- **Objetivo:** revisar uptime y cumplimiento de SLA.
- **Precondición:** monitoreo cloud activo (CU-O51, CU-T09).
- **Flujo principal:** 1) Abre tablero de SLA. 2) Revisa uptime e incidentes. 3) Decide acciones.
- **Flujo alternativo:** incumplimiento → enlace a incidentes (CU-O54).
- **Criterio de aceptación:** Dado el periodo, Cuando consulta SLA, Entonces visualiza uptime y cumplimiento (KPI-07/08).

### CU-E07 — Revisar crecimiento por marketplace y APIs
- **Actor:** A07, A08. **Paquete:** P10/P09. **OE/OT:** OE2/OT2.
- **Objetivo:** medir crecimiento del ecosistema.
- **Precondición:** datos de consumo de APIs y marketplace (CU-O49).
- **Flujo principal:** 1) Abre tablero de ecosistema. 2) Revisa APIs, integraciones e ingresos. 3) Analiza tendencia.
- **Flujo alternativo:** segmenta por partner.
- **Criterio de aceptación:** Dado el periodo, Cuando consulta el ecosistema, Entonces muestra KPI-04/05/06 legibles.

### CU-E08 — Generar reporte ejecutivo corporativo
- **Actor:** A07. **Paquete:** P08/P12. **OE/OT:** OE4/OT4.
- **Objetivo:** consolidar un informe ejecutivo.
- **Precondición:** KPIs y tableros disponibles.
- **Flujo principal:** 1) Selecciona plantilla ejecutiva. 2) Define alcance/periodo. 3) El sistema genera el informe. 4) Exporta (auditado).
- **Flujo alternativo:** programación periódica del reporte.
- **Criterio de aceptación:** Dado un periodo, Cuando genera el reporte ejecutivo, Entonces obtiene un documento consolidado, legible y exportable.

### CU-E09 — Analizar expansión geográfica institucional
- **Actor:** A07, A08. **Paquete:** P12/P09. **OE/OT:** OE1/OT1.
- **Objetivo:** identificar oportunidades de expansión por jurisdicción.
- **Precondición:** datos de instituciones por región.
- **Flujo principal:** 1) Abre mapa de expansión. 2) Filtra por país/jurisdicción. 3) Analiza cobertura y potencial.
- **Flujo alternativo:** jurisdicción sin datos → aviso.
- **Criterio de aceptación:** Dado un mapa, Cuando filtra por jurisdicción, Entonces visualiza cobertura y potencial legibles.

### CU-E10 — Aprobar roadmap estratégico del producto
- **Actor:** A07. **Paquete:** P12. **OE/OT:** OE4/OT4.
- **Objetivo:** registrar, versionar y aprobar el roadmap.
- **Precondición:** propuesta de roadmap disponible.
- **Flujo principal:** 1) Revisa iniciativas. 2) Prioriza según OE1–OE4. 3) Aprueba y versiona. 4) Queda auditado.
- **Flujo alternativo:** devolución para ajustes.
- **Criterio de aceptación:** Dado el roadmap, Cuando se aprueba, Entonces queda versionado y auditado.

---

# Casos de Uso Tácticos (CU-T)

### CU-T01 — Gestionar campañas Growth Hacking B2G
- **Actor:** A09 Especialista Growth. **Paquete:** P09. **OE/OT:** OE1/OT1.
- **Objetivo:** crear y medir campañas de adquisición institucional.
- **Precondición:** segmentos y leads disponibles.
- **Flujo principal:** 1) Crea campaña. 2) Define segmento y canal. 3) Lanza y mide resultados.
- **Flujo alternativo:** A/B testing de mensajes.
- **Criterio de aceptación:** Dado un gerente/growth, Cuando crea una campaña, Entonces queda registrada, segmentada y medible (KPI-02).

### CU-T02 — Administrar pipeline institucional
- **Actor:** A08 Gerente Comercial. **Paquete:** P09. **OE/OT:** OE1/OT1.
- **Objetivo:** gestionar etapas y oportunidades.
- **Precondición:** leads calificados (CU-O42).
- **Flujo principal:** 1) Visualiza pipeline. 2) Mueve oportunidades de etapa. 3) Registra avances.
- **Flujo alternativo:** oportunidad perdida → motivo y archivo.
- **Criterio de aceptación:** Dado el pipeline, Cuando actualiza una etapa, Entonces refleja el avance y recalcula forecast de ventas.

### CU-T03 — Gestionar demos y pruebas piloto
- **Actor:** A08. **Paquete:** P09. **OE/OT:** OE1/OT1.
- **Objetivo:** coordinar demos/pilotos con instituciones.
- **Precondición:** oportunidad activa.
- **Flujo principal:** 1) Programa demo (CU-O43). 2) Ejecuta piloto. 3) Registra resultados.
- **Flujo alternativo:** piloto extendido.
- **Criterio de aceptación:** Dada una oportunidad, Cuando agenda y ejecuta un piloto, Entonces queda registrado con resultados.

### CU-T04 — Gestionar licitaciones y RFP
- **Actor:** A08, A15 Legal. **Paquete:** P09. **OE/OT:** OE1/OT1.
- **Objetivo:** seguir procesos de licitación pública.
- **Precondición:** RFP identificado.
- **Flujo principal:** 1) Registra RFP. 2) Da seguimiento a hitos. 3) Adjunta documentos. 4) Registra resultado.
- **Flujo alternativo:** RFP cancelado por la entidad.
- **Criterio de aceptación:** Dado un RFP, Cuando registra avances, Entonces el sistema mantiene el historial y documentos.

### CU-T05 — Configurar catálogo de APIs
- **Actor:** A10 SRE. **Paquete:** P10. **OE/OT:** OE2/OT2.
- **Objetivo:** publicar y versionar APIs.
- **Precondición:** especificación de API disponible.
- **Flujo principal:** 1) Registra API. 2) Define versión y documentación. 3) Publica en catálogo.
- **Flujo alternativo:** versión deprecada.
- **Criterio de aceptación:** Dada una API nueva, Cuando se publica, Entonces queda versionada y documentada (OE2).

### CU-T06 — Gestionar integraciones con sistemas externos
- **Actor:** A10, A14 Sistema Externo. **Paquete:** P10. **OE/OT:** OE2/OT2.
- **Objetivo:** configurar conectores e integraciones.
- **Precondición:** credenciales aprovisionadas.
- **Flujo principal:** 1) Crea integración. 2) Configura conector/webhook. 3) Prueba conectividad.
- **Flujo alternativo:** error de credenciales → reintento seguro.
- **Criterio de aceptación:** Dada una integración, Cuando se configura, Entonces se valida la conectividad y queda auditada.

### CU-T07 — Gestionar marketplace y planes SaaS
- **Actor:** A08. **Paquete:** P10. **OE/OT:** OE2/OT2.
- **Objetivo:** administrar planes/ofertas del marketplace.
- **Precondición:** catálogo de productos.
- **Flujo principal:** 1) Crea plan SaaS. 2) Define precios y límites. 3) Publica.
- **Flujo alternativo:** plan promocional.
- **Criterio de aceptación:** Dado un plan, Cuando se publica, Entonces aparece disponible en el marketplace (KPI-06).

### CU-T08 — Configurar roles y permisos institucionales
- **Actor:** A01 Administrador. **Paquete:** P02/P01. **OE/OT:** OT5.
- **Objetivo:** definir RBAC por institución.
- **Precondición:** institución registrada.
- **Flujo principal:** 1) Crea/edita rol. 2) Asigna permisos (privilegio mínimo). 3) Guarda con auditoría.
- **Flujo alternativo:** clonado de rol.
- **Criterio de aceptación:** Dado un administrador, Cuando configura roles, Entonces los permisos aplican con privilegio mínimo y quedan auditados.

### CU-T09 — Gestionar SLA y monitoreo cloud
- **Actor:** A10 SRE. **Paquete:** P11. **OE/OT:** OE3/OT3.
- **Objetivo:** definir umbrales y monitoreo.
- **Precondición:** infraestructura cloud disponible.
- **Flujo principal:** 1) Define umbrales SLA. 2) Configura alertas. 3) Monitorea.
- **Flujo alternativo:** umbral inconsistente → validación.
- **Criterio de aceptación:** Dado un SRE, Cuando define umbrales, Entonces el monitoreo genera alertas al incumplirse (KPI-08).

### CU-T10 — Gestionar data warehouse corporativo
- **Actor:** A11 Analista BI. **Paquete:** P12. **OE/OT:** OE4/OT4.
- **Objetivo:** administrar fuentes, calidad y linaje del DWH.
- **Precondición:** fuentes identificadas.
- **Flujo principal:** 1) Registra fuente. 2) Define transformación/linaje. 3) Carga y valida calidad.
- **Flujo alternativo:** fuente con baja calidad → cuarentena.
- **Criterio de aceptación:** Dada una fuente, Cuando se integra, Entonces el DWH refleja datos con calidad y linaje (KPI-12).

### CU-T11 — Configurar indicadores KPI y tableros
- **Actor:** A11. **Paquete:** P12/P04. **OE/OT:** OE4/OT4.
- **Objetivo:** definir KPIs y armar tableros.
- **Precondición:** DWH poblado.
- **Flujo principal:** 1) Define KPI (fórmula/medida). 2) Crea tablero. 3) Publica para roles.
- **Flujo alternativo:** KPI calculado vs. directo.
- **Criterio de aceptación:** Dado un KPI, Cuando se configura, Entonces aparece en el tablero correspondiente y es legible.

### CU-T12 — Gestionar auditoría y cumplimiento
- **Actor:** A05 Auditor. **Paquete:** P03. **OE/OT:** OT5.
- **Objetivo:** revisar cumplimiento y configurar políticas de auditoría.
- **Precondición:** logs disponibles.
- **Flujo principal:** 1) Define políticas. 2) Revisa eventos. 3) Genera reporte de cumplimiento.
- **Flujo alternativo:** hallazgo → caso de cumplimiento.
- **Criterio de aceptación:** Dado un auditor, Cuando revisa el periodo, Entonces obtiene evidencia de cumplimiento (KPI-18/19).

### CU-T13 — Gestionar paquetes de producto por cliente
- **Actor:** A08. **Paquete:** P09. **OE/OT:** OE1/OE2.
- **Objetivo:** definir qué capacidades incluye cada cliente.
- **Precondición:** catálogo de capacidades.
- **Flujo principal:** 1) Selecciona cliente. 2) Arma paquete. 3) Asocia a contrato/licencia.
- **Flujo alternativo:** upsell de capacidades.
- **Criterio de aceptación:** Dado un cliente, Cuando se arma su paquete, Entonces sus capacidades disponibles reflejan el contrato (RN-07).

### CU-T14 — Administrar contratos y licencias B2G
- **Actor:** A08, A15. **Paquete:** P09/P02. **OE/OT:** OE1/OT1.
- **Objetivo:** gestionar contratos y vigencia de licencias.
- **Precondición:** institución y plan definidos.
- **Flujo principal:** 1) Registra contrato. 2) Define vigencia y SLA. 3) Activa licencias.
- **Flujo alternativo:** renovación/terminación.
- **Criterio de aceptación:** Dado un contrato, Cuando se activa, Entonces habilita las capacidades contratadas y queda auditado.

### CU-T15 — Gestionar onboarding y capacitación institucional
- **Actor:** A12 Customer Success. **Paquete:** P09. **OE/OT:** OE1/OT1.
- **Objetivo:** activar y capacitar al nuevo cliente.
- **Precondición:** contrato activo.
- **Flujo principal:** 1) Crea plan de onboarding. 2) Ejecuta capacitación. 3) Verifica adopción.
- **Flujo alternativo:** onboarding asistido extendido.
- **Criterio de aceptación:** Dado un cliente nuevo, Cuando completa onboarding, Entonces queda activo y capacitado.

### CU-T16 — Gestionar soporte postventa y success
- **Actor:** A12. **Paquete:** P09. **OE/OT:** OE1/OT1.
- **Objetivo:** atender soporte y asegurar retención.
- **Precondición:** cliente activo.
- **Flujo principal:** 1) Registra caso. 2) Da seguimiento. 3) Cierra con satisfacción.
- **Flujo alternativo:** escalamiento técnico (P11).
- **Criterio de aceptación:** Dado un caso de soporte, Cuando se resuelve, Entonces se cierra con registro y métrica de satisfacción.

---

# Casos de Uso Operativos (CU-O)

## P01 — Autenticación y Seguridad (OP1)

### CU-O01 — Iniciar sesión
- **Actor:** A06 Usuario Institucional. **Paquete:** P01. **OE/OT:** habilitador/OT5.
- **Objetivo:** obtener una sesión autenticada.
- **Precondición:** usuario registrado y activo.
- **Flujo principal:** 1) Ingresa credenciales. 2) El sistema valida. 3) Solicita MFA si aplica. 4) Crea sesión y registra bitácora (CU-O11).
- **Flujo alternativo:** credenciales inválidas → mensaje y conteo de intentos.
- **Criterio de aceptación:** Dado un usuario válido, Cuando inicia sesión con MFA, Entonces obtiene sesión válida y queda registrado.

### CU-O02 — Gestionar autenticación multifactor
- **Actor:** A06/A01. **Paquete:** P01. **OE/OT:** habilitador/OT5.
- **Objetivo:** configurar/validar segundo factor.
- **Precondición:** usuario autenticado en primer factor.
- **Flujo principal:** 1) Registra/usa factor MFA. 2) El sistema verifica. 3) Habilita acceso.
- **Flujo alternativo:** factor perdido → recuperación segura.
- **Criterio de aceptación:** Dado un rol crítico, Cuando inicia sesión, Entonces el sistema exige y valida MFA (RS-04).

### CU-O03 — Recuperar contraseña
- **Actor:** A06. **Paquete:** P01. **OE/OT:** habilitador/OT5.
- **Objetivo:** restablecer acceso de forma segura.
- **Precondición:** cuenta existente.
- **Flujo principal:** 1) Solicita recuperación. 2) Verifica identidad. 3) Restablece y notifica.
- **Flujo alternativo:** enlace expirado → nuevo intento.
- **Criterio de aceptación:** Dado un usuario, Cuando solicita recuperación verificada, Entonces puede establecer nueva contraseña y queda auditado.

### CU-O04 — Gestionar sesiones activas
- **Actor:** A01/A06. **Paquete:** P01. **OE/OT:** habilitador/OT5.
- **Objetivo:** ver y revocar sesiones.
- **Precondición:** sesiones existentes.
- **Flujo principal:** 1) Lista sesiones. 2) Revoca la deseada. 3) Registra acción.
- **Flujo alternativo:** revocación masiva.
- **Criterio de aceptación:** Dado un conjunto de sesiones, Cuando se revoca una, Entonces queda invalidada y auditada.

### CU-O05 — Validar permisos por rol
- **Actor:** A06 (verificado por sistema). **Paquete:** P01. **OE/OT:** habilitador/OT5.
- **Objetivo:** autorizar acciones según RBAC.
- **Precondición:** rol con permisos definidos.
- **Flujo principal:** 1) Usuario solicita acción. 2) El sistema verifica permiso en backend. 3) Permite o deniega.
- **Flujo alternativo:** permiso insuficiente → denegado y auditado.
- **Criterio de aceptación:** Dada una acción sensible, Cuando el rol no tiene permiso, Entonces se deniega y se registra (RS-02).

## P02 — Administración del Sistema (OP2)

### CU-O06 — Registrar institución cliente
- **Actor:** A01. **Paquete:** P02. **OE/OT:** OE1/OT1.
- **Objetivo:** dar de alta un tenant institucional.
- **Precondición:** contrato/aprobación comercial.
- **Flujo principal:** 1) Captura datos de la institución. 2) Configura aislamiento (tenant). 3) Activa.
- **Flujo alternativo:** datos incompletos → guardado parcial.
- **Criterio de aceptación:** Dada una institución nueva, Cuando se registra, Entonces queda activa con aislamiento de datos (RN-06).

### CU-O07 — Gestionar usuarios y roles
- **Actor:** A01. **Paquete:** P02. **OE/OT:** habilitador/OT5.
- **Objetivo:** administrar cuentas y asignación de roles.
- **Precondición:** institución activa.
- **Flujo principal:** 1) Crea/edita usuario. 2) Asigna rol. 3) Notifica y audita.
- **Flujo alternativo:** desactivación de usuario.
- **Criterio de aceptación:** Dado un usuario, Cuando se le asigna un rol, Entonces obtiene los permisos del rol y queda auditado.

### CU-O08 — Configurar parámetros y catálogos
- **Actor:** A01. **Paquete:** P02. **OE/OT:** habilitador/OT5.
- **Objetivo:** administrar parámetros del sistema y catálogos.
- **Precondición:** permisos de administración.
- **Flujo principal:** 1) Edita parámetro/catálogo. 2) Valida. 3) Persiste con auditoría.
- **Flujo alternativo:** valor fuera de rango → rechazo.
- **Criterio de aceptación:** Dado un parámetro, Cuando se guarda un valor válido, Entonces se aplica y se audita.

### CU-O09 — Gestionar licencias y planes
- **Actor:** A01/A08. **Paquete:** P02. **OE/OT:** OE1/OE2.
- **Objetivo:** asignar licencias/planes a instituciones.
- **Precondición:** plan definido (CU-T07).
- **Flujo principal:** 1) Selecciona plan. 2) Asigna licencias. 3) Activa capacidades.
- **Flujo alternativo:** suspensión por impago.
- **Criterio de aceptación:** Dada una licencia, Cuando se activa, Entonces habilita las capacidades contratadas (RN-07).

### CU-O10 — Registrar contrato y SLA
- **Actor:** A08/A15. **Paquete:** P02. **OE/OT:** OE1/OE3.
- **Objetivo:** registrar contrato y compromisos de servicio.
- **Precondición:** institución y plan.
- **Flujo principal:** 1) Registra contrato. 2) Define SLA. 3) Activa vigencia.
- **Flujo alternativo:** addendum contractual.
- **Criterio de aceptación:** Dado un contrato, Cuando se registra con SLA, Entonces queda vigente y vinculado al cliente.

## P03 — Auditoría y Trazabilidad (OP3)

> **CU-O11…CU-O15 se conservan, completan y amplían** (no cambian de código). Su versión ampliada
> se integra al modelo centralizado de auditoría descrito en los casos nuevos CU-O61…CU-O76
> (ver sección **"CASOS DE USO NUEVOS — NIVEL AUDITORÍA (P03)"** y `003-operativo/P03-auditoria/`).

### CU-O11 — Registrar bitácora de acceso
- **Actor:** Sistema (disparado por A06). **Paquete:** P03. **OE/OT:** habilitador/OT5.
- **Objetivo:** registrar accesos y eventos.
- **Precondición:** evento auditable ocurre.
- **Flujo principal:** 1) Captura evento. 2) Registra usuario/fecha/origen/resultado. 3) Almacena inmutable.
- **Flujo alternativo:** evento de alto riesgo → alerta.
- **Criterio de aceptación:** Dado un acceso, Cuando ocurre, Entonces queda un registro inmutable y atribuible (RS-05).

### CU-O12 — Consultar trazabilidad de actividad
- **Actor:** A05 Auditor. **Paquete:** P03. **OE/OT:** habilitador/OT5.
- **Objetivo:** reconstruir la actividad de un usuario/recurso.
- **Precondición:** logs existentes.
- **Flujo principal:** 1) Filtra por usuario/recurso/fecha. 2) El sistema muestra la traza. 3) Analiza.
- **Flujo alternativo:** sin resultados → aviso.
- **Criterio de aceptación:** Dado un filtro, Cuando consulta, Entonces obtiene la traza completa y legible.

### CU-O13 — Exportar logs de auditoría
- **Actor:** A05. **Paquete:** P03. **OE/OT:** habilitador/OT5.
- **Objetivo:** exportar evidencia de auditoría.
- **Precondición:** permiso de exportación.
- **Flujo principal:** 1) Selecciona rango. 2) Exporta. 3) La exportación queda auditada.
- **Flujo alternativo:** exportación cifrada.
- **Criterio de aceptación:** Dado un rango, Cuando se exporta, Entonces se genera un archivo íntegro y la acción queda registrada (RN-08).

### CU-O14 — Generar alerta de manipulación
- **Actor:** Sistema/A05. **Paquete:** P03. **OE/OT:** habilitador/OT5.
- **Objetivo:** detectar y alertar manipulación de datos/evidencias.
- **Precondición:** verificación de integridad activa.
- **Flujo principal:** 1) Detecta inconsistencia (hash/log). 2) Genera alerta. 3) Notifica y registra.
- **Flujo alternativo:** falso positivo → revisión.
- **Criterio de aceptación:** Dada una inconsistencia de integridad, Cuando se detecta, Entonces se emite alerta y se preserva el historial (RN-02).

### CU-O15 — Validar cadena de custodia
- **Actor:** A05/A04. **Paquete:** P03. **OE/OT:** habilitador/OT5.
- **Objetivo:** verificar la integridad de la custodia de una evidencia.
- **Precondición:** evidencia con historial de custodia.
- **Flujo principal:** 1) Selecciona evidencia. 2) El sistema valida la cadena. 3) Muestra resultado.
- **Flujo alternativo:** ruptura detectada → alerta (CU-O14).
- **Criterio de aceptación:** Dada una evidencia, Cuando se valida su custodia, Entonces el sistema confirma integridad o reporta ruptura (RS-07).

## P04 — Dashboard y Analítica Criminal (OP4)

### CU-O16 — Visualizar mapa de calor criminal
- **Actor:** A03 Analista Criminal. **Paquete:** P04. **OE/OT:** OE4/OT4.
- **Objetivo:** ver concentración geográfica de delitos.
- **Precondición:** datos georreferenciados.
- **Flujo principal:** 1) Abre mapa. 2) Aplica filtros (zona/tipo/fecha). 3) Visualiza densidad.
- **Flujo alternativo:** sin datos en el área → aviso.
- **Criterio de aceptación:** Dado un filtro, Cuando consulta el mapa, Entonces se muestra un mapa de calor legible y proporcionado (RI-04).

### CU-O17 — Consultar indicadores criminales
- **Actor:** A03. **Paquete:** P04. **OE/OT:** OE4/OT4.
- **Objetivo:** ver indicadores delictivos clave.
- **Precondición:** datos consolidados.
- **Flujo principal:** 1) Abre panel. 2) Selecciona indicadores. 3) Analiza.
- **Flujo alternativo:** comparación entre periodos.
- **Criterio de aceptación:** Dado un periodo, Cuando consulta indicadores, Entonces obtiene valores correctos y legibles.

### CU-O18 — Ejecutar filtros analíticos
- **Actor:** A03. **Paquete:** P04. **OE/OT:** OE4/OT4.
- **Objetivo:** segmentar la información analítica.
- **Precondición:** dataset disponible.
- **Flujo principal:** 1) Define filtros. 2) Aplica. 3) Visualiza resultado.
- **Flujo alternativo:** combinación sin resultados.
- **Criterio de aceptación:** Dado un conjunto de filtros, Cuando se aplican, Entonces los resultados reflejan exactamente los criterios.

### CU-O19 — Consultar tendencias delictivas
- **Actor:** A03. **Paquete:** P04. **OE/OT:** OE4/OT4.
- **Objetivo:** analizar evolución temporal.
- **Precondición:** series históricas.
- **Flujo principal:** 1) Selecciona dimensión temporal. 2) Visualiza tendencia. 3) Interpreta.
- **Flujo alternativo:** estacionalidad.
- **Criterio de aceptación:** Dado un rango, Cuando consulta tendencias, Entonces obtiene una serie legible y proporcionada.

### CU-O20 — Generar predicción criminal
- **Actor:** A03. **Paquete:** P04. **OE/OT:** OE4/OT4.
- **Objetivo:** estimar incidencia futura.
- **Precondición:** datos suficientes y modelo definido (PC-O2).
- **Flujo principal:** 1) Selecciona modelo/horizonte. 2) Ejecuta predicción. 3) Visualiza con incertidumbre.
- **Flujo alternativo:** datos insuficientes → aviso.
- **Criterio de aceptación:** Dado un horizonte, Cuando ejecuta la predicción, Entonces obtiene una estimación con su nivel de confianza.

## P05 — Gestión de Expedientes (OP5)

### CU-O21 — Crear expediente criminal
- **Actor:** A02 Investigador. **Paquete:** P05. **OE/OT:** OE4/OT6.
- **Objetivo:** abrir un caso.
- **Precondición:** permiso de creación.
- **Flujo principal:** 1) Captura datos del caso. 2) El sistema asigna folio único y estado inicial. 3) Audita.
- **Flujo alternativo:** guardado como borrador.
- **Criterio de aceptación:** Dado un investigador autorizado, Cuando crea un expediente, Entonces se genera con folio único, estado inicial y auditoría.

### CU-O22 — Asignar investigador a expediente
- **Actor:** A01/A02. **Paquete:** P05. **OE/OT:** OE4/OT6.
- **Objetivo:** asignar responsable.
- **Precondición:** expediente existente.
- **Flujo principal:** 1) Selecciona expediente. 2) Asigna investigador. 3) Notifica y audita.
- **Flujo alternativo:** reasignación.
- **Criterio de aceptación:** Dado un expediente, Cuando se asigna un investigador, Entonces queda registrado como responsable.

### CU-O23 — Actualizar estado del expediente
- **Actor:** A02. **Paquete:** P05. **OE/OT:** OE4/OT6.
- **Objetivo:** reflejar avance del caso.
- **Precondición:** expediente abierto.
- **Flujo principal:** 1) Cambia estado. 2) Registra motivo. 3) Audita.
- **Flujo alternativo:** transición no permitida → bloqueo.
- **Criterio de aceptación:** Dado un expediente, Cuando se cambia su estado válido, Entonces se actualiza y se audita.

### CU-O24 — Vincular delitos, evidencias e involucrados
- **Actor:** A02. **Paquete:** P05. **OE/OT:** OE4/OT6.
- **Objetivo:** relacionar entidades del caso.
- **Precondición:** entidades existentes.
- **Flujo principal:** 1) Selecciona expediente. 2) Vincula delito/evidencia/involucrado. 3) Audita.
- **Flujo alternativo:** desvinculación con motivo.
- **Criterio de aceptación:** Dado un expediente, Cuando se vinculan entidades, Entonces las relaciones quedan registradas y trazables.

### CU-O25 — Cerrar expediente criminal
- **Actor:** A02/A01. **Paquete:** P05. **OE/OT:** OE4/OT6.
- **Objetivo:** finalizar un caso.
- **Precondición:** criterios de completitud y custodia cumplidos (RN-09).
- **Flujo principal:** 1) Solicita cierre. 2) El sistema valida completitud. 3) Cierra y audita.
- **Flujo alternativo:** reapertura justificada.
- **Criterio de aceptación:** Dado un expediente incompleto, Cuando se intenta cerrar, Entonces el sistema lo impide (RN-09).

## P06 — Gestión de Evidencias Digitales (OP6)

### CU-O26 — Registrar evidencia digital
- **Actor:** A04 Custodio. **Paquete:** P06. **OE/OT:** OE4/OT6.
- **Objetivo:** dar de alta una evidencia.
- **Precondición:** expediente asociado.
- **Flujo principal:** 1) Captura metadatos. 2) Crea registro. 3) Inicia cadena de custodia.
- **Flujo alternativo:** evidencia provisional.
- **Criterio de aceptación:** Dada una evidencia, Cuando se registra, Entonces se crea con metadatos y custodia inicial.

### CU-O27 — Cargar archivo de evidencia
- **Actor:** A04. **Paquete:** P06. **OE/OT:** OE4/OT6.
- **Objetivo:** adjuntar el archivo digital.
- **Precondición:** evidencia registrada.
- **Flujo principal:** 1) Sube archivo. 2) El sistema almacena de forma segura. 3) Dispara cálculo de hash (CU-O28).
- **Flujo alternativo:** archivo corrupto → rechazo.
- **Criterio de aceptación:** Dada una evidencia, Cuando se carga el archivo, Entonces se almacena cifrado y se registra.

### CU-O28 — Calcular hash de evidencia
- **Actor:** Sistema. **Paquete:** P06. **OE/OT:** OE4/OT6.
- **Objetivo:** garantizar integridad criptográfica.
- **Precondición:** archivo cargado.
- **Flujo principal:** 1) Calcula hash. 2) Lo asocia a la evidencia. 3) Audita.
- **Flujo alternativo:** recálculo de verificación.
- **Criterio de aceptación:** Dado un archivo, Cuando se calcula su hash, Entonces queda almacenado y verificable (KPI-21).

### CU-O29 — Gestionar custodia de evidencia
- **Actor:** A04. **Paquete:** P06. **OE/OT:** OE4/OT6.
- **Objetivo:** registrar transferencias de custodia.
- **Precondición:** evidencia con custodia iniciada.
- **Flujo principal:** 1) Registra transferencia. 2) Asocia responsable y momento. 3) Audita sin sobrescribir historial.
- **Flujo alternativo:** custodia temporal.
- **Criterio de aceptación:** Dada una transferencia, Cuando se registra, Entonces la cadena se actualiza sin perder el historial previo (RN-02).

### CU-O30 — Consultar evidencia autorizada
- **Actor:** A02/A05. **Paquete:** P06. **OE/OT:** OE4/OT6.
- **Objetivo:** acceder a evidencia con permiso.
- **Precondición:** permiso y evidencia existente.
- **Flujo principal:** 1) Solicita acceso. 2) El sistema valida permiso. 3) Muestra evidencia y registra acceso.
- **Flujo alternativo:** sin permiso → denegado.
- **Criterio de aceptación:** Dada una evidencia, Cuando un usuario autorizado la consulta, Entonces accede y el acceso queda auditado.

## P07 — Gestión de Involucrados (OP7)

### CU-O31 — Registrar víctima
- **Actor:** A02. **Paquete:** P07. **OE/OT:** OE4/OT6.
- **Objetivo:** registrar a una víctima.
- **Precondición:** permiso de registro.
- **Flujo principal:** 1) Captura datos. 2) Crea registro. 3) Audita.
- **Flujo alternativo:** datos sensibles protegidos.
- **Criterio de aceptación:** Dada una víctima, Cuando se registra, Entonces queda almacenada con protección de datos.

### CU-O32 — Registrar sospechoso
- **Actor:** A02. **Paquete:** P07. **OE/OT:** OE4/OT6.
- **Objetivo:** registrar a un sospechoso.
- **Precondición:** permiso de registro.
- **Flujo principal:** 1) Captura datos. 2) Crea registro. 3) Audita.
- **Flujo alternativo:** alias múltiples.
- **Criterio de aceptación:** Dado un sospechoso, Cuando se registra, Entonces queda almacenado y vinculable a un expediente.

### CU-O33 — Registrar testigo
- **Actor:** A02. **Paquete:** P07. **OE/OT:** OE4/OT6.
- **Objetivo:** registrar a un testigo.
- **Precondición:** permiso de registro.
- **Flujo principal:** 1) Captura datos. 2) Crea registro. 3) Audita.
- **Flujo alternativo:** testigo protegido/anónimo.
- **Criterio de aceptación:** Dado un testigo, Cuando se registra, Entonces queda almacenado con su nivel de protección.

### CU-O34 — Vincular involucrado a expediente
- **Actor:** A02. **Paquete:** P07. **OE/OT:** OE4/OT6.
- **Objetivo:** relacionar persona con caso.
- **Precondición:** involucrado y expediente existentes.
- **Flujo principal:** 1) Selecciona involucrado. 2) Define rol en el caso. 3) Vincula y audita.
- **Flujo alternativo:** un involucrado en varios casos.
- **Criterio de aceptación:** Dado un involucrado, Cuando se vincula a un expediente, Entonces la relación queda trazable (KPI-23).

### CU-O35 — Consultar historial de involucrado
- **Actor:** A02/A03. **Paquete:** P07. **OE/OT:** OE4/OT6.
- **Objetivo:** ver antecedentes y vínculos.
- **Precondición:** involucrado con historial.
- **Flujo principal:** 1) Busca involucrado. 2) El sistema muestra su historial y casos. 3) Analiza.
- **Flujo alternativo:** sin antecedentes.
- **Criterio de aceptación:** Dado un involucrado, Cuando se consulta su historial, Entonces se muestran sus vínculos autorizados.

## P08 — Reportería y Exportación (OP8)

### CU-O36 — Generar reporte operativo
- **Actor:** A02/A06. **Paquete:** P08. **OE/OT:** OE4/OT6.
- **Objetivo:** producir un reporte de operación.
- **Precondición:** datos disponibles y permiso.
- **Flujo principal:** 1) Selecciona tipo y filtros. 2) Genera reporte. 3) Visualiza.
- **Flujo alternativo:** reporte pesado → generación asíncrona.
- **Criterio de aceptación:** Dado un tipo de reporte, Cuando se genera, Entonces el contenido es correcto y legible.

### CU-O37 — Exportar reporte PDF/Excel
- **Actor:** A02/A06. **Paquete:** P08. **OE/OT:** OE4/OT6.
- **Objetivo:** exportar a formatos estándar.
- **Precondición:** reporte generado y permiso.
- **Flujo principal:** 1) Elige formato. 2) Exporta. 3) La exportación queda auditada.
- **Flujo alternativo:** exportación protegida con marca de agua.
- **Criterio de aceptación:** Dado un reporte, Cuando se exporta a PDF/Excel, Entonces el archivo es legible, completo y auditado (RN-08).

### CU-O38 — Programar reporte automático
- **Actor:** A01/A06. **Paquete:** P08. **OE/OT:** OE4/OT6.
- **Objetivo:** automatizar reportes recurrentes.
- **Precondición:** plantilla y permisos.
- **Flujo principal:** 1) Define periodicidad. 2) Configura destinatarios. 3) Activa programación.
- **Flujo alternativo:** pausa de programación.
- **Criterio de aceptación:** Dada una programación, Cuando llega la hora, Entonces el reporte se genera y distribuye automáticamente.

### CU-O39 — Emitir informe institucional
- **Actor:** A06. **Paquete:** P08. **OE/OT:** OE4/OT6.
- **Objetivo:** producir un informe formal institucional.
- **Precondición:** datos validados.
- **Flujo principal:** 1) Selecciona plantilla institucional. 2) Genera. 3) Firma/valida.
- **Flujo alternativo:** revisión previa.
- **Criterio de aceptación:** Dado un informe institucional, Cuando se emite, Entonces cumple el formato oficial y queda registrado.

### CU-O40 — Enviar reporte autorizado
- **Actor:** A06. **Paquete:** P08. **OE/OT:** OE4/OT6.
- **Objetivo:** distribuir un reporte a destinatarios autorizados.
- **Precondición:** reporte aprobado.
- **Flujo principal:** 1) Selecciona destinatarios autorizados. 2) Envía. 3) Audita envío.
- **Flujo alternativo:** destinatario no autorizado → bloqueo.
- **Criterio de aceptación:** Dado un reporte aprobado, Cuando se envía, Entonces solo llega a destinatarios autorizados y se audita.

## P09 — Gestión Comercial B2G (OP9)

### CU-O41 — Registrar lead B2G
- **Actor:** A09/A08. **Paquete:** P09. **OE/OT:** OE1/OT1.
- **Objetivo:** capturar un prospecto institucional.
- **Precondición:** fuente de lead identificada.
- **Flujo principal:** 1) Captura datos del lead. 2) Asigna origen. 3) Registra.
- **Flujo alternativo:** lead duplicado → fusión.
- **Criterio de aceptación:** Dado un lead, Cuando se registra, Entonces queda disponible para calificación (KPI-02).

### CU-O42 — Calificar oportunidad institucional
- **Actor:** A08. **Paquete:** P09. **OE/OT:** OE1/OT1.
- **Objetivo:** evaluar el potencial del lead.
- **Precondición:** lead registrado.
- **Flujo principal:** 1) Evalúa criterios. 2) Asigna puntaje/etapa. 3) Convierte en oportunidad.
- **Flujo alternativo:** descalificación con motivo.
- **Criterio de aceptación:** Dado un lead, Cuando se califica, Entonces se clasifica y entra al pipeline (CU-T02).

### CU-O43 — Programar demo institucional
- **Actor:** A08. **Paquete:** P09. **OE/OT:** OE1/OT1.
- **Objetivo:** agendar una demostración.
- **Precondición:** oportunidad activa.
- **Flujo principal:** 1) Selecciona oportunidad. 2) Agenda demo. 3) Notifica.
- **Flujo alternativo:** reprogramación.
- **Criterio de aceptación:** Dada una oportunidad, Cuando se agenda una demo, Entonces queda registrada con fecha y participantes.

### CU-O44 — Registrar avance de licitación/RFP
- **Actor:** A08/A15. **Paquete:** P09. **OE/OT:** OE1/OT1.
- **Objetivo:** registrar hitos de un proceso de licitación.
- **Precondición:** RFP registrado (CU-T04).
- **Flujo principal:** 1) Registra hito/documento. 2) Actualiza estado. 3) Audita.
- **Flujo alternativo:** prórroga del proceso.
- **Criterio de aceptación:** Dado un RFP, Cuando se registra un avance, Entonces el historial refleja el hito con su fecha.

### CU-O45 — Generar propuesta comercial B2G
- **Actor:** A08. **Paquete:** P09. **OE/OT:** OE1/OT1.
- **Objetivo:** producir una propuesta para la institución.
- **Precondición:** oportunidad calificada y paquete definido (CU-T13).
- **Flujo principal:** 1) Selecciona plantilla. 2) Configura alcance/precio. 3) Genera propuesta.
- **Flujo alternativo:** propuesta revisada por legal.
- **Criterio de aceptación:** Dada una oportunidad, Cuando se genera la propuesta, Entonces el documento refleja el paquete y es legible.

## P10 — Ecosistema de APIs (OP10)

### CU-O46 — Registrar API key institucional
- **Actor:** A10/A14. **Paquete:** P10. **OE/OT:** OE2/OT2.
- **Objetivo:** emitir credenciales de API para una institución.
- **Precondición:** institución con plan que incluye APIs.
- **Flujo principal:** 1) Genera API key. 2) Asigna scopes. 3) Entrega de forma segura.
- **Flujo alternativo:** revocación de key.
- **Criterio de aceptación:** Dada una institución, Cuando se emite una API key, Entonces queda activa con scopes y auditada.

### CU-O47 — Consultar documentación API
- **Actor:** A14/A10. **Paquete:** P10. **OE/OT:** OE2/OT2.
- **Objetivo:** acceder a la documentación del catálogo.
- **Precondición:** API publicada (CU-T05).
- **Flujo principal:** 1) Abre portal de APIs. 2) Busca endpoint. 3) Consulta especificación y ejemplos.
- **Flujo alternativo:** versión anterior.
- **Criterio de aceptación:** Dada una API publicada, Cuando se consulta su documentación, Entonces se muestra versionada y legible.

### CU-O48 — Configurar webhook institucional
- **Actor:** A10/A14. **Paquete:** P10. **OE/OT:** OE2/OT2.
- **Objetivo:** suscribir eventos a un endpoint externo.
- **Precondición:** API key válida.
- **Flujo principal:** 1) Define evento y URL destino. 2) Valida y prueba. 3) Activa.
- **Flujo alternativo:** reintentos ante fallo de entrega.
- **Criterio de aceptación:** Dado un webhook, Cuando se configura, Entonces se validan eventos de prueba y queda activo.

### CU-O49 — Registrar consumo API
- **Actor:** Sistema. **Paquete:** P10. **OE/OT:** OE2/OT2.
- **Objetivo:** medir uso de las APIs.
- **Precondición:** llamadas a API.
- **Flujo principal:** 1) Registra llamada. 2) Asocia institución y endpoint. 3) Acumula métricas.
- **Flujo alternativo:** límite excedido → throttling.
- **Criterio de aceptación:** Dada una llamada, Cuando se procesa, Entonces el consumo se contabiliza (KPI-05/06).

### CU-O50 — Gestionar conector externo
- **Actor:** A10. **Paquete:** P10. **OE/OT:** OE2/OT2.
- **Objetivo:** administrar conectores de integración.
- **Precondición:** integración definida (CU-T06).
- **Flujo principal:** 1) Configura conector. 2) Prueba. 3) Activa/monitorea.
- **Flujo alternativo:** desactivación.
- **Criterio de aceptación:** Dado un conector, Cuando se gestiona, Entonces su estado y salud quedan registrados.

## P11 — Gestión Cloud y SLA (OP11)

### CU-O51 — Monitorear uptime del servicio
- **Actor:** A10 SRE. **Paquete:** P11. **OE/OT:** OE3/OT3.
- **Objetivo:** vigilar la disponibilidad.
- **Precondición:** monitoreo configurado (CU-T09).
- **Flujo principal:** 1) Observa métricas de uptime. 2) Detecta anomalías. 3) Actúa.
- **Flujo alternativo:** caída → alerta e incidente (CU-O54).
- **Criterio de aceptación:** Dado el servicio, Cuando se monitorea, Entonces el uptime se mide y reporta (KPI-07).

### CU-O52 — Ejecutar backup programado
- **Actor:** Sistema/A10. **Paquete:** P11. **OE/OT:** OE3/OT3.
- **Objetivo:** respaldar datos según calendario.
- **Precondición:** política de backup definida (PC-O3).
- **Flujo principal:** 1) Llega la hora programada. 2) Ejecuta backup. 3) Verifica y registra en historial.
- **Flujo alternativo:** backup manual.
- **Criterio de aceptación:** Dada una programación, Cuando llega la hora, Entonces el backup se ejecuta y queda registrado.

### CU-O53 — Activar escalamiento automático
- **Actor:** Sistema/A10. **Paquete:** P11. **OE/OT:** OE3/OT3.
- **Objetivo:** ajustar recursos según demanda.
- **Precondición:** reglas de autoescalado.
- **Flujo principal:** 1) Detecta carga elevada. 2) Escala recursos. 3) Registra evento.
- **Flujo alternativo:** desescalado al bajar la carga.
- **Criterio de aceptación:** Dada una carga alta, Cuando se supera el umbral, Entonces el sistema escala automáticamente.

### CU-O54 — Registrar incidente SLA
- **Actor:** A10. **Paquete:** P11. **OE/OT:** OE3/OT3.
- **Objetivo:** documentar incumplimientos de servicio.
- **Precondición:** incidente detectado.
- **Flujo principal:** 1) Registra incidente. 2) Clasifica severidad. 3) Da seguimiento hasta cierre.
- **Flujo alternativo:** incidente mayor → DR (CU-O55).
- **Criterio de aceptación:** Dado un incidente, Cuando se registra, Entonces afecta el cálculo de cumplimiento (KPI-08).

### CU-O55 — Ejecutar recuperación ante desastres
- **Actor:** A10. **Paquete:** P11. **OE/OT:** OE3/OT3.
- **Objetivo:** restaurar el servicio tras una contingencia.
- **Precondición:** plan de DR y respaldos disponibles.
- **Flujo principal:** 1) Activa plan DR. 2) Restaura desde respaldo. 3) Verifica RTO/RPO.
- **Flujo alternativo:** failover a región secundaria.
- **Criterio de aceptación:** Dada una contingencia, Cuando se ejecuta DR, Entonces el servicio se restaura dentro de RTO/RPO (KPI-09).

## P12 — Gobierno de Datos e Inteligencia de Negocio (OP12)

### CU-O56 — Consolidar datos comerciales y de uso
- **Actor:** A11 Analista BI. **Paquete:** P12. **OE/OT:** OE4/OT4.
- **Objetivo:** integrar fuentes en el DWH.
- **Precondición:** fuentes registradas (CU-T10).
- **Flujo principal:** 1) Ejecuta consolidación. 2) Valida calidad/linaje. 3) Publica datasets.
- **Flujo alternativo:** carga incremental.
- **Criterio de aceptación:** Dadas las fuentes, Cuando se consolidan, Entonces el DWH refleja datos íntegros (KPI-12).

### CU-O57 — Calcular KPI corporativo
- **Actor:** Sistema/A11. **Paquete:** P12. **OE/OT:** OE4/OT4.
- **Objetivo:** computar indicadores definidos.
- **Precondición:** KPI definido (CU-T11) y datos disponibles.
- **Flujo principal:** 1) Aplica fórmula. 2) Calcula valor. 3) Publica en tablero.
- **Flujo alternativo:** recálculo histórico.
- **Criterio de aceptación:** Dado un KPI, Cuando se calcula, Entonces el valor es correcto y aparece en su tablero.

### CU-O58 — Generar benchmark institucional
- **Actor:** A11. **Paquete:** P12. **OE/OT:** OE4/OT4.
- **Objetivo:** comparar desempeño entre referencias.
- **Precondición:** datos comparables.
- **Flujo principal:** 1) Selecciona dimensiones. 2) Calcula benchmark. 3) Publica.
- **Flujo alternativo:** anonimización de comparados.
- **Criterio de aceptación:** Dadas las dimensiones, Cuando se genera el benchmark, Entonces se muestra comparativa legible (KPI-11).

### CU-O59 — Exportar tablero ejecutivo
- **Actor:** A07/A11. **Paquete:** P12. **OE/OT:** OE4/OT4.
- **Objetivo:** exportar tableros para uso ejecutivo.
- **Precondición:** tablero disponible y permiso.
- **Flujo principal:** 1) Selecciona tablero. 2) Exporta (PDF/imagen/datos). 3) Audita.
- **Flujo alternativo:** exportación programada.
- **Criterio de aceptación:** Dado un tablero, Cuando se exporta, Entonces el archivo conserva legibilidad y proporción (RI-04).

### CU-O60 — Ejecutar modelo forecast de demanda B2G
- **Actor:** A11. **Paquete:** P12. **OE/OT:** OE4/OT4.
- **Objetivo:** pronosticar demanda comercial.
- **Precondición:** datos históricos y modelo definido (PC-O2).
- **Flujo principal:** 1) Selecciona horizonte. 2) Ejecuta forecast. 3) Visualiza con confianza.
- **Flujo alternativo:** escenarios (optimista/base/pesimista).
- **Criterio de aceptación:** Dado un horizonte, Cuando se ejecuta el forecast, Entonces se obtiene una proyección con su precisión (KPI-11).

---

# CASOS DE USO NUEVOS — NIVEL AUDITORÍA (P03)

> **Implementado adicional.** Amplían el paquete **P03 — Auditoría y Trazabilidad** sin eliminar ni
> cambiar CU-O11…CU-O15. Cada caso incluye la estructura completa de 18 puntos exigida: código,
> nombre, objetivo, actor principal, actores secundarios, paquete UML, precondiciones, entradas,
> flujo principal, flujos alternativos, excepciones, salidas, reglas de negocio, requisitos
> funcionales, requisitos no funcionales, criterios de aceptación (Dado/Cuando/Entonces),
> dependencias y fuera de alcance. Actor principal por defecto: **A05 Auditor / Oficial de
> Cumplimiento**; actor disparador frecuente: **Sistema**. Detalle de arquitectura y modelo de
> datos en `003-operativo/P03-auditoria/spec.md`.

### CU-O61 — Registrar operaciones CRUD del sistema
- **Código:** CU-O61. **Paquete UML:** P03. **OE/OT:** habilitador/OT5.
- **Objetivo:** registrar toda operación de escritura del sistema (INSERT, UPDATE, DELETE, consulta sensible, restauración, cambio de estado, asignación, vinculación, desvinculación) con valores antes/después.
- **Actor principal:** Sistema (auditoría automática). **Actores secundarios:** A06 Usuario Institucional, A05 Auditor.
- **Precondiciones:** usuario autenticado con sesión válida; servicio de auditoría disponible.
- **Entradas:** contexto de la operación (usuario, sesión, módulo, caso de uso, entidad, tabla, id de registro, valores previos y nuevos, motivo si aplica).
- **Flujo principal:** 1) El servicio ejecuta una operación de escritura. 2) El decorador `@audited` captura valores antes/después. 3) `AuditService.record()` normaliza, enmascara datos sensibles y calcula `event_hash`+`previous_hash`. 4) Persiste append-only en `audit_events` (+ `audit_event_changes`). 5) Devuelve sin bloquear la operación (escritura asíncrona).
- **Flujos alternativos:** FA1 eliminación → se conserva copia histórica del valor borrado. FA2 operación masiva → genera evento `BULK_OPERATION` y posible alerta.
- **Excepciones:** EX1 fallo del servicio de auditoría → encola en buffer y genera alerta (no se pierde el evento). EX2 dato sensible no enmascarable → se omite el valor y se marca.
- **Salidas:** evento de auditoría inmutable con diferencias antes/después.
- **Reglas de negocio:** RN-02, RS-05; logs append-only; tiempo en servidor UTC.
- **Requisitos funcionales:** RF-O-P03-01, RF-O-P03-02, RF-O-P03-03.
- **Requisitos no funcionales:** RNF-O-P03-01, RNF-O-P03-05, RNF-O-P03-07.
- **Criterio de aceptación:** Dado un INSERT/UPDATE/DELETE sobre una entidad, Cuando se ejecuta, Entonces se registra un evento inmutable con usuario, rol, registro afectado y valores anterior/nuevo.
- **Dependencias:** P01 (sesión/JWT), núcleo de auditoría (Etapa 1).
- **Fuera de alcance:** RBAC fino (se registra el rol efectivo).

### CU-O62 — Auditar autenticación y sesiones
- **Código:** CU-O62. **Paquete UML:** P03. **OE/OT:** habilitador/OT5.
- **Objetivo:** registrar todo el ciclo de autenticación y sesión: login exitoso/fallido, logout manual/expiración/administrativo, revocación, bloqueo/desbloqueo, recuperación y cambio de contraseña, MFA (activación/validación/fallo), inicio/fin/duración de sesión, última actividad, inactividad, sesiones simultáneas, dispositivo, IP, navegador y SO.
- **Actor principal:** Sistema. **Actores secundarios:** A06 Usuario, A01 Administrador, A05 Auditor.
- **Precondiciones:** servicio de autenticación operativo.
- **Entradas:** credenciales/eventos de sesión, IP, User-Agent, método de autenticación, estado MFA.
- **Flujo principal:** 1) Ocurre un evento de auth/sesión. 2) `AuthService` lo notifica a `AuditService`. 3) Se registra en `audit_events` y se actualiza `audit_sessions` (inicio, última actividad, cierre, duración). 4) Se calcula duración al cerrar.
- **Flujos alternativos:** FA1 cierre administrativo de sesión → motivo `admin_cerrada`. FA2 expiración → motivo `expirada`.
- **Excepciones:** EX1 múltiples intentos fallidos → bloqueo + alerta (FASE 5). EX2 fallo MFA reiterado → alerta.
- **Salidas:** eventos de sesión y registro de duración total.
- **Reglas de negocio:** RS-04 (MFA roles críticos), append-only, UTC.
- **Requisitos funcionales:** RF-O-P03-04, RF-O-P03-05.
- **Requisitos no funcionales:** RNF-O-P03-01, RNF-O-P03-04.
- **Criterio de aceptación:** Dado un inicio y cierre de sesión, Cuando ocurren, Entonces se registran inicio, última actividad, cierre y duración, con IP, dispositivo y navegador.
- **Dependencias:** P01.
- **Fuera de alcance:** implementación de MFA (se audita cuando exista).

### CU-O63 — Auditar roles, permisos y privilegios
- **Código:** CU-O63. **Paquete UML:** P03. **OE/OT:** habilitador/OT5.
- **Objetivo:** registrar creación/modificación/eliminación de roles, asignación/retiro de roles, cambios de permisos, elevación de privilegios, accesos denegados, intentos no autorizados, cambios por administradores y el rol efectivo usado en cada operación.
- **Actor principal:** Sistema. **Actores secundarios:** A01 Administrador, A05 Auditor.
- **Precondiciones:** módulo de administración de roles disponible.
- **Entradas:** rol, permiso, usuario afectado, administrador responsable, resultado.
- **Flujo principal:** 1) Se ejecuta una acción de RBAC. 2) Se captura antes/después. 3) Se registra evento con rol efectivo y resultado.
- **Flujos alternativos:** FA1 acceso denegado por permiso → evento `ACCESS_DENIED`.
- **Excepciones:** EX1 elevación de privilegios → alerta de seguridad.
- **Salidas:** evento de cambio de RBAC con rol efectivo.
- **Reglas de negocio:** RS-02 (denegar sin permiso), privilegio mínimo.
- **Requisitos funcionales:** RF-O-P03-05.
- **Requisitos no funcionales:** RNF-O-P03-01, RNF-O-P03-03.
- **Criterio de aceptación:** Dada una asignación de rol o un acceso denegado, Cuando ocurre, Entonces queda registrado con usuario, administrador, permiso y resultado.
- **Dependencias:** P02, RBAC.
- **Fuera de alcance:** activar el RBAC fino (PC-A6).

### CU-O64 — Auditar acceso a información sensible
- **Código:** CU-O64. **Paquete UML:** P03. **OE/OT:** habilitador/OT5.
- **Objetivo:** registrar el acceso a información sensible (expedientes, evidencias, víctimas, sospechosos, testigos, información personal/reservada, cadena de custodia, informes, datos analíticos restringidos, documentos clasificados), distinguiendo el modo (consulta, visualización, descarga, impresión, exportación, modificación, eliminación, compartición).
- **Actor principal:** Sistema. **Actores secundarios:** A02 Investigador, A03 Analista, A05 Auditor.
- **Precondiciones:** entidad clasificada como sensible.
- **Entradas:** entidad, id de registro, modo de acceso, clasificación.
- **Flujo principal:** 1) Un usuario accede a un recurso sensible. 2) El helper `audit_access` registra el evento y el modo. 3) Se persiste en `audit_access_events` ligado a `audit_events`.
- **Flujos alternativos:** FA1 descarga/exportación → además registra en `audit_exports`.
- **Excepciones:** EX1 acceso repetido a expedientes no asignados → alerta.
- **Salidas:** evento de acceso con modo y clasificación.
- **Reglas de negocio:** RS-03 (mínimo privilegio), enmascaramiento.
- **Requisitos funcionales:** RF-O-P03-06.
- **Requisitos no funcionales:** RNF-O-P03-03, RNF-O-P03-07.
- **Criterio de aceptación:** Dado un acceso a información sensible, Cuando se realiza, Entonces se registra quién, qué registro y el modo (consulta/descarga/exportación…).
- **Dependencias:** P05, P06, P07, P08.
- **Fuera de alcance:** clasificación automática de sensibilidad (se usa la definida).

### CU-O65 — Auditar expedientes criminales
- **Código:** CU-O65. **Paquete UML:** P03. **OE/OT:** OE4/OT6.
- **Objetivo:** registrar el ciclo de vida del expediente: creación, usuario creador, investigador asignado, reasignaciones, cambios de estado y motivo, delitos/evidencias/involucrados vinculados y desvinculados, intentos de cierre, cierre aprobado/rechazado, reapertura y motivo, e historial completo.
- **Actor principal:** Sistema. **Actores secundarios:** A02 Investigador, A01 Administrador, A05 Auditor.
- **Precondiciones:** módulo de expedientes (P05) operativo.
- **Entradas:** expediente, usuario, estado, motivo, entidades vinculadas.
- **Flujo principal:** 1) Ocurre una operación sobre el expediente. 2) Se captura antes/después y motivo. 3) Se registra evento trazable al folio del caso.
- **Flujos alternativos:** FA1 cierre rechazado → se registra motivo. FA2 reapertura → motivo obligatorio.
- **Excepciones:** EX1 transición de estado inválida → evento `ACCESS_DENIED`/rechazo.
- **Salidas:** historial completo del expediente reconstruible.
- **Reglas de negocio:** RN-09 (cierre con completitud).
- **Requisitos funcionales:** RF-O-P03-01, RF-O-P03-02.
- **Requisitos no funcionales:** RNF-O-P03-01.
- **Criterio de aceptación:** Dado un cambio de estado o reasignación de expediente, Cuando ocurre, Entonces el historial registra el antes/después, el usuario y el motivo.
- **Dependencias:** P05, CU-O61.
- **Fuera de alcance:** lógica de negocio del expediente (solo se audita).

### CU-O66 — Auditar evidencias y cadena de custodia
- **Código:** CU-O66. **Paquete UML:** P03. **OE/OT:** OE4/OT6.
- **Objetivo:** registrar registro de evidencia, carga de archivo (nombre, tamaño, MIME), hash inicial y recálculo, resultado de verificación, custodio inicial, transferencias (fecha/hora, custodio anterior/nuevo, motivo, ubicación), descargas/consultas, rupturas de cadena, intentos de modificación, eliminaciones bloqueadas y alertas de integridad.
- **Actor principal:** Sistema. **Actores secundarios:** A04 Custodio, A02 Investigador, A05 Auditor.
- **Precondiciones:** módulo de evidencias (P06) operativo.
- **Entradas:** evidencia, archivo, hash, custodios, motivo de transferencia.
- **Flujo principal:** 1) Se registra/transfiere una evidencia. 2) Se calcula/recalcula hash. 3) Se registra evento en `audit_evidence_events` y la transferencia en `audit_custody_events`.
- **Flujos alternativos:** FA1 recálculo de verificación periódica.
- **Excepciones:** EX1 hash no coincide → `CUSTODY_BROKEN` + alerta (habilita CU-O14/CU-O15). EX2 intento de eliminar evidencia → bloqueo + registro.
- **Salidas:** cadena de custodia trazable e íntegra.
- **Reglas de negocio:** RS-07, RN-02.
- **Requisitos funcionales:** RF-O-P03-13.
- **Requisitos no funcionales:** RNF-O-P03-02.
- **Criterio de aceptación:** Dada una transferencia de custodia, Cuando se registra, Entonces se conserva custodio anterior/nuevo, fecha, motivo y el hash verificable; una ruptura genera alerta.
- **Dependencias:** P06, CU-O28 (hash), CU-O15.
- **Fuera de alcance:** almacenamiento físico de la evidencia.

### CU-O67 — Auditar involucrados
- **Código:** CU-O67. **Paquete UML:** P03. **OE/OT:** OE4/OT6.
- **Objetivo:** registrar creación de víctimas/sospechosos/testigos, actualización de información, acceso a datos protegidos, cambios de nivel de confidencialidad, vinculación/desvinculación a expedientes, usuario responsable, motivo y valores anterior/nuevo.
- **Actor principal:** Sistema. **Actores secundarios:** A02 Investigador, A05 Auditor.
- **Precondiciones:** módulo de involucrados (P07) operativo.
- **Entradas:** involucrado, datos protegidos, nivel de confidencialidad, expediente.
- **Flujo principal:** 1) Operación sobre involucrado. 2) Captura antes/después y motivo. 3) Registra evento (acceso a datos protegidos vía CU-O64).
- **Flujos alternativos:** FA1 cambio de confidencialidad → evento específico.
- **Excepciones:** EX1 acceso a dato protegido sin permiso → denegado y registrado.
- **Salidas:** historial de cambios del involucrado.
- **Reglas de negocio:** protección de datos personales, enmascaramiento.
- **Requisitos funcionales:** RF-O-P03-01, RF-O-P03-06.
- **Requisitos no funcionales:** RNF-O-P03-07.
- **Criterio de aceptación:** Dada una actualización de un involucrado, Cuando ocurre, Entonces se registra el responsable, el motivo y los valores anterior/nuevo enmascarados.
- **Dependencias:** P07, CU-O64.
- **Fuera de alcance:** anonimización irreversible.

### CU-O68 — Auditar reportes, archivos y exportaciones
- **Código:** CU-O68. **Paquete UML:** P03. **OE/OT:** OE4/OT6.
- **Objetivo:** registrar generación de reportes (tipo, parámetros/filtros, rango de fechas, solicitante, formato), exportaciones PDF/Excel, descargas, impresiones, envío por correo y destinatarios, programación automática, cancelaciones, resultado, tamaño del archivo, marca de agua y motivo de exportación de información sensible.
- **Actor principal:** Sistema. **Actores secundarios:** A06 Usuario, A05 Auditor.
- **Precondiciones:** módulo de reportería (P08) operativo.
- **Entradas:** parámetros del reporte, formato, destinatarios, motivo.
- **Flujo principal:** 1) Se genera/exporta un reporte. 2) Se registra en `audit_exports` ligado a `audit_events`. 3) Se aplica marca de agua si corresponde.
- **Flujos alternativos:** FA1 programación automática. FA2 cancelación de exportación.
- **Excepciones:** EX1 exportación masiva → alerta.
- **Salidas:** evento de exportación auditado.
- **Reglas de negocio:** RN-08 (exportaciones auditadas).
- **Requisitos funcionales:** RF-O-P03-01 (extiende CU-O13).
- **Requisitos no funcionales:** RNF-O-P03-03.
- **Criterio de aceptación:** Dada una exportación, Cuando se realiza, Entonces se registra el solicitante, formato, parámetros, destinatarios y motivo (si es sensible).
- **Dependencias:** P08, CU-O13.
- **Fuera de alcance:** entrega/transporte del correo.

### CU-O69 — Auditar administración y configuración
- **Código:** CU-O69. **Paquete UML:** P03. **OE/OT:** habilitador/OT5.
- **Objetivo:** registrar cambios de parámetros y catálogos, registro/modificación de instituciones, configuración multi-tenant, activación/desactivación de módulos, cambios de licencia/plan/SLA, configuración de almacenamiento y seguridad, políticas de retención y activación/desactivación de funcionalidades.
- **Actor principal:** Sistema. **Actores secundarios:** A01 Administrador, A05 Auditor.
- **Precondiciones:** módulo de administración (P02) operativo.
- **Entradas:** parámetro/catálogo/configuración, valor anterior y nuevo.
- **Flujo principal:** 1) Se cambia una configuración. 2) Se captura antes/después. 3) Se registra evento `CONFIG_CHANGED`.
- **Flujos alternativos:** FA1 cambio de licencia/plan/SLA.
- **Excepciones:** EX1 cambio de configuración crítica → alerta.
- **Salidas:** evento de configuración auditado.
- **Reglas de negocio:** append-only, UTC.
- **Requisitos funcionales:** RF-O-P03-01.
- **Requisitos no funcionales:** RNF-O-P03-01.
- **Criterio de aceptación:** Dado un cambio de parámetro o configuración, Cuando se guarda, Entonces se registra el responsable y los valores anterior/nuevo.
- **Dependencias:** P02.
- **Fuera de alcance:** implementación de multi-tenant (PC-A2).

### CU-O70 — Auditar APIs e integraciones
- **Código:** CU-O70. **Paquete UML:** P03. **OE/OT:** OE2/OT2.
- **Objetivo:** registrar creación/revocación/rotación de API keys, scopes, institución propietaria, endpoint consumido, método HTTP, código de respuesta, tiempo de respuesta, IP, sistema externo, datos transferidos, errores de integración, fallos de autenticación, webhooks enviados/fallidos, reintentos y conectores activados/desactivados. **Nunca** registra tokens, contraseñas, secretos ni API keys completas.
- **Actor principal:** Sistema. **Actores secundarios:** A10 SRE, A14 Sistema Externo, A05 Auditor.
- **Precondiciones:** ecosistema de APIs (P10) operativo.
- **Entradas:** referencia parcial de API key, scopes, endpoint, método, código, latencia.
- **Flujo principal:** 1) Se consume una API o gestiona una key. 2) El middleware registra en `audit_api_events`. 3) Se enmascaran/omiten secretos.
- **Flujos alternativos:** FA1 webhook fallido → reintentos registrados.
- **Excepciones:** EX1 API key comprometida o consumo fuera de límite → alerta.
- **Salidas:** evento de API sin secretos.
- **Reglas de negocio:** RS-06 (no almacenar secretos), enmascaramiento.
- **Requisitos funcionales:** RF-O-P03-14.
- **Requisitos no funcionales:** RNF-O-P03-07.
- **Criterio de aceptación:** Dada una llamada API, Cuando se procesa, Entonces se registra endpoint, método, código y latencia sin almacenar el token/API key completos.
- **Dependencias:** P10.
- **Fuera de alcance:** rate limiting (solo se audita).

### CU-O71 — Auditar infraestructura cloud y continuidad
- **Código:** CU-O71. **Paquete UML:** P03. **OE/OT:** OE3/OT3.
- **Objetivo:** registrar eventos de monitoreo, caídas, reinicios, escalamiento/desescalamiento, creación/eliminación de recursos, ejecución y resultado de backups, restauraciones, recuperación ante desastres, incidentes SLA (severidad, tiempos de detección/respuesta/resolución, RTO/RPO logrados), cambios de configuración cloud y usuario/proceso responsable.
- **Actor principal:** Sistema. **Actores secundarios:** A10 SRE, A05 Auditor.
- **Precondiciones:** gestión cloud (P11) operativa.
- **Entradas:** evento de infraestructura, severidad, tiempos, responsable.
- **Flujo principal:** 1) Ocurre un evento cloud/continuidad. 2) Se registra evento (`BACKUP_*`, `RESTORE_*`, `SLA_INCIDENT`). 3) Se asocia responsable.
- **Flujos alternativos:** FA1 escalamiento automático.
- **Excepciones:** EX1 backup fallido / restauración no autorizada → alerta.
- **Salidas:** evento de continuidad auditado.
- **Reglas de negocio:** trazabilidad de continuidad.
- **Requisitos funcionales:** RF-O-P03-01.
- **Requisitos no funcionales:** RNF-O-P03-08.
- **Criterio de aceptación:** Dada una ejecución de backup o un incidente SLA, Cuando ocurre, Entonces se registra el resultado, los tiempos y el responsable.
- **Dependencias:** P11.
- **Fuera de alcance:** ejecución del backup/DR (solo se audita).

### CU-O72 — Auditar analítica, BI e inteligencia artificial
- **Código:** CU-O72. **Paquete UML:** P03. **OE/OT:** OE4/OT4.
- **Objetivo:** registrar consultas a dashboards, filtros aplicados, KPI consultados/recalculados, exportación de tableros, ejecución de modelos predictivos (modelo, versión, parámetros, dataset, fecha, resultado, nivel de confianza, solicitante), cambios en fórmulas de KPI, cambios en fuentes de datos y ejecuciones fallidas.
- **Actor principal:** Sistema. **Actores secundarios:** A03 Analista, A11 Analista BI, A05 Auditor.
- **Precondiciones:** analítica (P04/P12) operativa.
- **Entradas:** consulta/modelo, parámetros, dataset, versión.
- **Flujo principal:** 1) Se ejecuta una consulta/modelo. 2) Se registra evento con parámetros y resultado. 3) Se versiona el modelo usado.
- **Flujos alternativos:** FA1 recálculo de KPI.
- **Excepciones:** EX1 ejecución fallida → registrada con error controlado.
- **Salidas:** evento analítico trazable.
- **Reglas de negocio:** trazabilidad de fórmulas y datasets.
- **Requisitos funcionales:** RF-O-P03-01, RF-O-P03-06.
- **Requisitos no funcionales:** RNF-O-P03-06.
- **Criterio de aceptación:** Dada una ejecución de modelo predictivo, Cuando se realiza, Entonces se registra modelo, versión, parámetros, dataset y resultado.
- **Dependencias:** P04, P12.
- **Fuera de alcance:** entrenamiento de modelos.

### CU-O73 — Consultar tablero central de auditoría
- **Código:** CU-O73. **Paquete UML:** P03. **OE/OT:** habilitador/OT5.
- **Objetivo:** permitir buscar/filtrar eventos por usuario, rol, institución, módulo, caso de uso, entidad, registro, operación, IP, sesión, rango de fechas, resultado, nivel de riesgo y evento de seguridad; visualizar línea de tiempo, comparar antes/después, ver duración de sesiones, acciones por usuario/módulo, accesos denegados y eventos críticos.
- **Actor principal:** A05 Auditor / Oficial de Cumplimiento. **Actores secundarios:** A01 Administrador (limitado).
- **Precondiciones:** eventos registrados; rol Auditor/Compliance; endpoint de consulta implementado.
- **Entradas:** filtros de búsqueda.
- **Flujo principal:** 1) El auditor abre el tablero. 2) Aplica filtros avanzados. 3) El sistema devuelve resultados paginados, línea de tiempo y detalle antes/después, respetando aislamiento multi-tenant.
- **Flujos alternativos:** FA1 sin resultados → aviso. FA2 ver detalle de un evento → reconstrucción completa.
- **Excepciones:** EX1 usuario sin rol Auditor → acceso denegado y auditado.
- **Salidas:** vista de auditoría consultable y reconstrucción de operaciones.
- **Reglas de negocio:** solo Auditor/Compliance; aislamiento multi-tenant.
- **Requisitos funcionales:** RF-O-P03-09 (extiende CU-O12).
- **Requisitos no funcionales:** RNF-O-P03-03, RNF-O-P03-06, RNF-O-P03-09.
- **Criterio de aceptación:** Dado un auditor, Cuando filtra por usuario/rol/sesión/módulo/CU/entidad/fecha/IP, Entonces obtiene la traza completa, paginada y legible.
- **Dependencias:** núcleo de auditoría, paquete `auditoria_trazabilidad` (hoy vacío).
- **Fuera de alcance:** edición de eventos (son inmutables).

### CU-O74 — Generar reportes de auditoría y cumplimiento
- **Código:** CU-O74. **Paquete UML:** P03. **OE/OT:** habilitador/OT5.
- **Objetivo:** generar reportes de actividad por usuario/rol/institución/módulo, sesiones, operaciones CRUD, eliminaciones, cambios críticos, accesos a información sensible, exportaciones, evidencias, cadena de custodia, fallos de autenticación, accesos denegados, actividad fuera de horario, alertas, integridad y cumplimiento.
- **Actor principal:** A05 Auditor / Oficial de Cumplimiento. **Actores secundarios:** A07 Ejecutivo (lectura).
- **Precondiciones:** eventos disponibles; permiso de reporte.
- **Entradas:** tipo de reporte, periodo, filtros.
- **Flujo principal:** 1) Selecciona el tipo de reporte. 2) Define periodo/filtros. 3) Genera y exporta de forma **autorizada y auditada** (la exportación queda registrada).
- **Flujos alternativos:** FA1 programación periódica del reporte.
- **Excepciones:** EX1 sin permiso → denegado.
- **Salidas:** reporte de cumplimiento exportable y auditado.
- **Reglas de negocio:** RN-08; toda exportación se audita.
- **Requisitos funcionales:** RF-O-P03-10 (extiende CU-O13).
- **Requisitos no funcionales:** RNF-O-P03-03, RNF-O-P03-09.
- **Criterio de aceptación:** Dado un periodo, Cuando genera un reporte de cumplimiento, Entonces obtiene un documento legible y la exportación queda registrada.
- **Dependencias:** CU-O73, CU-O68.
- **Fuera de alcance:** envío externo a SIEM (extensión futura).

### CU-O75 — Verificar integridad de la auditoría
- **Código:** CU-O75. **Paquete UML:** P03. **OE/OT:** habilitador/OT5.
- **Objetivo:** validar que los logs no fueron modificados: hash por evento, relación con el hash anterior, detección de ruptura de cadena, validación de firma/sello de tiempo, verificaciones periódicas, generación de evidencias de integridad y notificación de cualquier alteración.
- **Actor principal:** Sistema (job programado). **Actores secundarios:** A05 Auditor.
- **Precondiciones:** eventos con `event_hash`/`previous_hash`.
- **Entradas:** rango de eventos a verificar.
- **Flujo principal:** 1) Un job (Celery beat) recorre la cadena. 2) Recalcula y compara hashes. 3) Registra el resultado en `audit_integrity_checks`.
- **Flujos alternativos:** FA1 verificación bajo demanda por el auditor.
- **Excepciones:** EX1 ruptura de cadena → `SECURITY_ALERT` (amplía CU-O14).
- **Salidas:** evidencia de integridad y alertas ante alteración.
- **Reglas de negocio:** RN-02; inmutabilidad.
- **Requisitos funcionales:** RF-O-P03-07, RF-O-P03-08, RF-O-P03-11.
- **Requisitos no funcionales:** RNF-O-P03-02.
- **Criterio de aceptación:** Dada una manipulación de un log, Cuando se ejecuta la verificación, Entonces se detecta la ruptura de la cadena y se notifica.
- **Dependencias:** núcleo de auditoría, Celery beat.
- **Fuera de alcance:** firma con HSM externo (PC-A4).

### CU-O76 — Gestionar retención y archivado de auditoría
- **Código:** CU-O76. **Paquete UML:** P03. **OE/OT:** habilitador/OT5.
- **Objetivo:** definir políticas de retención, archivar logs antiguos, mantener acceso controlado a históricos, aplicar retención legal, suspender eliminación por investigación, registrar quién autorizó el archivado, registrar restauración de históricos y evitar eliminación manual no autorizada.
- **Actor principal:** A05 Auditor / Oficial de Cumplimiento. **Actores secundarios:** A01 Administrador.
- **Precondiciones:** políticas de retención definidas por institución.
- **Entradas:** política, rango a archivar, autorización.
- **Flujo principal:** 1) Se aplica la política de retención. 2) Se archivan logs antiguos en `audit_archives` conservando integridad. 3) Se registra quién autorizó.
- **Flujos alternativos:** FA1 suspensión de eliminación por investigación (retención legal). FA2 restauración de históricos.
- **Excepciones:** EX1 intento de eliminación manual no autorizada → bloqueo + alerta.
- **Salidas:** históricos archivados, accesibles y auditados.
- **Reglas de negocio:** retención configurable por institución; conservación legal de eventos críticos.
- **Requisitos funcionales:** RF-O-P03-12.
- **Requisitos no funcionales:** RNF-O-P03-01, RNF-O-P03-02.
- **Criterio de aceptación:** Dada una política de retención, Cuando vence un rango, Entonces los logs se archivan sin perder integridad y el archivado queda autorizado y registrado.
- **Dependencias:** núcleo de auditoría, almacenamiento (PC-A1).
- **Fuera de alcance:** borrado físico definitivo (sujeto a política legal).

---

## Pendientes por Confirmar (casos de uso)

- **PC-CU1:** Reglas de transición de estados del expediente (CU-O23/CU-O25).
- **PC-CU2:** Algoritmo de hash y verificación periódica (CU-O28).
- **PC-CU3:** Modelos analíticos para predicción/forecast (CU-O20/CU-O60).

## Notas de Reorganización (RC-01)

- No se detectaron casos de uso duplicados que deban eliminarse. CU-O44 (avance RFP operativo) y
  CU-T04 (gestión de RFP táctica) son **complementarios**, no duplicados: el primero registra
  hitos operativos; el segundo gobierna el proceso. Si en revisión se considerara solape, se
  **propone** consolidarlos en una vista única conservando ambos códigos (no se eliminan).
