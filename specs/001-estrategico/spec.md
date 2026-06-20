# Especificación — Nivel Estratégico

> Nivel empresarial **Estratégico**. Casos de uso CU-E01…CU-E10. Subordinada a la constitución
> y a `000-sistema-general/`. **Sin implementación de código.**

## 1. Objetivo

Especificar las capacidades de dirección corporativa que permiten gobernar el negocio B2G de
CrimeTrack Analytics Corp en función de los cuatro objetivos estratégicos OE1–OE4: medir y
decidir sobre adquisición de mercado, escalabilidad por ecosistemas/APIs, disponibilidad cloud
e inteligencia de negocio centralizada.

## 2. Contexto

La capa estratégica consume datos consolidados (de P09–P12 y P04) para producir cuadros de mando
(Balanced Scorecard), OKR, análisis de rentabilidad (ARR/MRR), ventaja competitiva, expansión
geográfica y aprobación de roadmap. Es la cara ejecutiva del producto B2G; no opera datos
criminalísticos crudos, sino indicadores e inteligencia agregada.

## 3. Actores

A07 Ejecutivo Corporativo / Dirección (principal), A08 Gerente Comercial B2G, A11 Analista BI,
A10 Ingeniero de Plataforma/SRE (para SLA), A01 Administrador (configuración de accesos).

## 4. Departamento Responsable

D01 Dirección Ejecutiva y Estrategia Corporativa (principal), con apoyo de D05 Inteligencia de
Negocio, D02 Comercial & Growth y D04 Operaciones Cloud.

## 5. Nivel Empresarial

Estratégico.

## 6. Paquete UML Relacionado

P12 Gobierno de Datos e Inteligencia de Negocio (principal), P04 Dashboard y Analítica,
P09 Comercial B2G, P10 Ecosistema de APIs, P11 Cloud y SLA, P08 Reportería.

## 7. Objetivos Relacionados

| OE | OT | Casos de uso estratégicos asociados |
|---|---|---|
| OE1 | OT1 | CU-E02, CU-E09 |
| OE2 | OT2 | CU-E07 |
| OE3 | OT3 | CU-E06 |
| OE4 | OT4 | CU-E01, CU-E03, CU-E04, CU-E05, CU-E08, CU-E10 |

## 8. Requisitos Funcionales

| ID | Requisito |
|---|---|
| RF-E-01 | Mostrar Balanced Scorecard con perspectivas financiera, cliente, procesos y aprendizaje (CU-E01). |
| RF-E-02 | Analizar penetración de mercado B2G por región y segmento (CU-E02). |
| RF-E-03 | Calcular y visualizar rentabilidad ARR/MRR gubernamental (CU-E03). |
| RF-E-04 | Registrar y dar seguimiento a OKR corporativos vinculados a KPIs (CU-E04). |
| RF-E-05 | Generar análisis de ventaja competitiva/benchmark (CU-E05). |
| RF-E-06 | Evaluar disponibilidad cloud y cumplimiento de SLA (CU-E06). |
| RF-E-07 | Mostrar crecimiento por marketplace y APIs (CU-E07). |
| RF-E-08 | Generar reporte ejecutivo corporativo consolidado (CU-E08). |
| RF-E-09 | Analizar expansión geográfica institucional (CU-E09). |
| RF-E-10 | Registrar, versionar y aprobar el roadmap estratégico del producto (CU-E10). |

## 9. Requisitos No Funcionales

| ID | Requisito |
|---|---|
| RNF-E-01 | Los tableros se actualizan con latencia de datos documentada (near-real-time o batch). |
| RNF-E-02 | Acceso restringido a roles ejecutivos con MFA. |
| RNF-E-03 | Gráficos legibles y proporcionados; exportables sin pérdida de legibilidad. |
| RNF-E-04 | Consultas analíticas optimizadas (respuesta interactiva en tableros). |
| RNF-E-05 | Auditoría de accesos y exportaciones ejecutivas. |

## 10. Reglas de Negocio

RN-01 (trazabilidad), RN-03 (alcance B2G), RN-04 (OE inmutables), RN-08 (exportación auditada).
Adicional: las metas/OKR no pueden contradecir OE1–OE4.

## 11. Entradas

Datos consolidados de negocio (ARR/MRR, pipeline, marketplace), métricas cloud (uptime/SLA),
indicadores criminales agregados, definiciones de OKR/metas, parámetros de benchmark.

## 12. Salidas

Cuadros de mando, reportes ejecutivos, OKR registrados, roadmap aprobado, análisis de mercado y
expansión, tableros de ecosistema y SLA.

## 13. Precondiciones

Usuario ejecutivo autenticado con MFA; data warehouse y KPIs configurados (CU-T10, CU-T11);
fuentes de datos integradas.

## 14. Flujo Principal

1. El ejecutivo accede al panel estratégico.
2. Selecciona la vista (BSC, mercado, ARR/MRR, OKR, competitividad, SLA, ecosistema).
3. El sistema consolida y presenta indicadores legibles.
4. El ejecutivo decide (define OKR, aprueba roadmap, genera reporte ejecutivo).
5. Las decisiones quedan registradas, versionadas y auditadas.

## 15. Flujos Alternativos

- **FA-E1:** datos parcialmente disponibles → se muestra cobertura y se marca el faltante.
- **FA-E2:** exportación de reporte ejecutivo → requiere permiso y queda auditada.

## 16. Excepciones

- **EX-E1:** fuente de datos no integrada → indicador no disponible con aviso.
- **EX-E2:** intento de modificar OE → bloqueado por regla RN-04.

## 17. Criterios de Aceptación (Dado / Cuando / Entonces)

- **CA-E-01** — Dado un ejecutivo autenticado con MFA, Cuando abre el Balanced Scorecard, Entonces
  visualiza las 4 perspectivas con datos vigentes y legibles.
- **CA-E-02** — Dado un periodo seleccionado, Cuando consulta ARR/MRR, Entonces obtiene el ingreso
  recurrente correcto y exportable.
- **CA-E-03** — Dado un OKR nuevo, Cuando lo registra, Entonces queda vinculado a uno o más KPIs y
  a un OE, sin contradecir OE1–OE4.
- **CA-E-04** — Dado el roadmap, Cuando se aprueba, Entonces queda versionado y auditado.

## 18. Dependencias

P12/P04 (datos y analítica), P09/P10/P11 (fuentes de negocio), CU-T10/CU-T11 (DWH y KPIs),
seguridad (P01) y auditoría (P03).

## 19. Fuera de Alcance

Operación criminalística directa; captura de datos crudos; implementación de modelos (solo se
especifica su consumo). Modificación de OE1–OE4.

## 20. Historias de Usuario Relacionadas

HU-E-01…HU-E-10 (ver `004-uml-documentacion/historias-usuario.md`).

## Pendientes por Confirmar

- **PC-E1:** Definición exacta de perspectivas y métricas del Balanced Scorecard del cliente.
- **PC-E2:** Periodicidad de actualización (near-real-time vs batch) por tablero.
