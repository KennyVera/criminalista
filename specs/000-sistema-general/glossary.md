# Glosario — CrimeTrack Analytics Corp

> Definiciones comunes para toda la documentación de especificaciones. En caso de ambigüedad,
> este glosario y la constitución prevalecen.

## Términos de Negocio (B2G)

| Término | Definición |
|---|---|
| B2G (Business-to-Government) | Modelo en el que la empresa vende su software a organismos gubernamentales. |
| Cliente Institucional | Organización gubernamental que adquiere y opera el sistema (tenant). |
| Growth Hacking B2G | Estrategias de adquisición automatizada de clientes institucionales (OE1). |
| Marketplace | Plataforma donde se ofrecen planes SaaS, APIs e integraciones del ecosistema (OE2). |
| ARR / MRR | Ingreso Recurrente Anual / Mensual; métricas de rentabilidad del negocio. |
| CAC | Costo de Adquisición de Cliente. |
| Pipeline institucional | Embudo de oportunidades comerciales con organismos gubernamentales. |
| RFP / Licitación | Solicitud formal de propuesta / proceso de contratación pública. |
| SLA | Acuerdo de Nivel de Servicio (disponibilidad, soporte, recuperación). |
| Balanced Scorecard | Cuadro de mando integral con perspectivas financiera, cliente, procesos y aprendizaje. |
| OKR | Objectives and Key Results; metas y resultados clave corporativos. |
| Tenant | Instancia lógica aislada de datos por institución cliente (multi-tenant). |
| Onboarding institucional | Proceso de alta, configuración y capacitación de un nuevo cliente. |
| Customer Success | Función que asegura adopción, retención y valor postventa. |

## Términos Criminalísticos (Producto)

| Término | Definición |
|---|---|
| Expediente Criminal | Caso que agrupa delitos, evidencias, involucrados y actuaciones de investigación. |
| Evidencia Digital | Archivo o dato con valor probatorio gestionado por el sistema. |
| Cadena de Custodia | Historial íntegro e inalterable de creación, acceso, modificación, transferencia y custodia de una evidencia, que preserva su validez legal. |
| Hash de Evidencia | Huella criptográfica que garantiza la integridad de un archivo de evidencia. |
| Involucrado | Persona vinculada a un expediente: víctima, sospechoso o testigo. |
| Analítica Criminal | Análisis de datos delictivos: indicadores, mapas de calor, tendencias y predicción. |
| Mapa de Calor Criminal | Visualización geográfica de densidad/concentración delictiva. |
| Predicción Criminal | Estimación de incidencia delictiva futura mediante modelos analíticos. |
| Custodio de Evidencia | Rol responsable de la guarda y transferencia de evidencias. |

## Términos de Arquitectura y SDD

| Término | Definición |
|---|---|
| Paquete UML | Agrupación cohesiva de funcionalidades con responsabilidad y contratos definidos (P01–P12). |
| Caso de Uso (CU) | Interacción entre actor(es) y el sistema para lograr un objetivo. Códigos CU-E/CU-T/CU-O. |
| Historia de Usuario (HU) | Necesidad expresada como "Como [actor], quiero [necesidad], para [beneficio]". |
| Requisito Funcional (RF) | Capacidad que el sistema debe proveer. |
| Requisito No Funcional (RNF) | Cualidad o restricción (rendimiento, seguridad, disponibilidad, etc.). |
| Criterio de Aceptación | Condición verificable, en formato Dado/Cuando/Entonces, para aceptar un elemento. |
| Matriz de Trazabilidad | Tabla que relaciona OE↔OT↔OP↔CU↔HU↔Paquete↔Actor↔Depto↔RF↔KPI↔Criterio↔Resultado. |
| Spec-Driven Development (SDD) | Metodología: especificar antes de implementar (constitución→spec→plan→tasks→implementación). |
| RBAC | Control de Acceso Basado en Roles. |
| MFA | Autenticación Multifactor. |
| RTO / RPO | Tiempo / Punto Objetivo de Recuperación ante desastres. |

## Códigos y Convenciones

| Prefijo | Significado |
|---|---|
| OE1–OE4 | Objetivos Estratégicos (inmutables). |
| OT1–OT6 | Objetivos Tácticos. |
| OP1–OP12 | Objetivos Operativos (uno por paquete operativo). |
| P01–P12 | Paquetes UML. |
| CU-E## | Caso de uso estratégico. |
| CU-T## | Caso de uso táctico. |
| CU-O## | Caso de uso operativo. |
| HU-E/T/O-## | Historia de usuario por nivel. |
| RF- / RNF- | Requisito funcional / no funcional. |
| RN-## | Regla de negocio. |
| A## / D## | Actor / Departamento. |
| KPI-## | Indicador clave de desempeño. |

## Estados de Elemento (gobierno SDD)

| Estado | Significado |
|---|---|
| Especificado | Documentado y trazable; aún no implementado. |
| Implementado adicional | Elemento agregado por necesidad detectada durante la especificación. |
| Pendiente por confirmar | Información faltante registrada para validación. |
| Propuesta de reorganización | Posible duplicidad señalada sin eliminar el elemento original. |
