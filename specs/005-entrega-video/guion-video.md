# Guion de Video — Demostración CrimeTrack Analytics Corp

> Guion para grabar la demostración del sistema **en ejecución**, mostrando **en simultáneo** el
> caso de uso documentado correspondiente (pantalla dividida: aplicación a la izquierda, documento
> `004/casos-uso.md` a la derecha). Enfoque B2G. Duración objetivo: 8–12 minutos.

## Formato de Grabación

- **Resolución:** 1080p mínimo; texto y gráficos **legibles** (RI-04, sin miniaturas ni deformaciones).
- **Pantalla dividida:** app en ejecución + caso de uso documentado visible al mismo tiempo.
- **Audio:** narración por escena. **Subtítulos:** opcionales en español.
- **Marcas:** mostrar el código del CU (p. ej., "CU-O21") en pantalla al iniciar cada escena.

## Estructura del Video

### Escena 0 — Introducción (0:00–0:45)
- Presentar: "CrimeTrack Analytics Corp — Sistema de Seguimiento, Gestión y Análisis de Crímenes (B2G)".
- Mencionar enfoque empresarial B2G y los objetivos OE1–OE4 (sin detenerse en exceso).
- Anunciar que cada función mostrada está documentada como caso de uso trazable.

### Escena 1 — CU-O01 Iniciar sesión (0:45–2:00)
- **Narración:** "Iniciamos sesión de forma segura; el sistema exige MFA para roles críticos."
- **Acción en app:** ingresar credenciales → validar MFA → acceder.
- **Documento visible:** CU-O01 (actor, flujo principal, criterio).
- **Cierre de escena:** mostrar el registro en bitácora (criterio cumplido).

### Escena 2 — CU-O21 Crear expediente criminal (2:00–3:30)
- **Narración:** "Creamos un expediente; el sistema asigna folio único y estado inicial."
- **Acción en app:** capturar datos → guardar → ver folio y auditoría.
- **Documento visible:** CU-O21.
- **Cierre:** folio único + auditoría (criterio cumplido).

### Escena 3 — CU-O31 / CU-O32 Registrar víctima y sospechoso (3:30–5:00)
- **Narración:** "Registramos involucrados y los vinculamos al expediente."
- **Acción en app:** alta de víctima (CU-O31) y sospechoso (CU-O32) → vincular (CU-O34).
- **Documento visible:** CU-O31 y CU-O32.
- **Cierre:** involucrados vinculados y trazables.

### Escena 4 — CU-O26 Registrar evidencia digital + hash (5:00–6:45)
- **Narración:** "Registramos una evidencia, cargamos su archivo y el sistema calcula su hash; así inicia la cadena de custodia."
- **Acción en app:** registrar evidencia (CU-O26) → cargar archivo (CU-O27) → ver hash (CU-O28).
- **Documento visible:** CU-O26 (+ referencia a CU-O27/CU-O28).
- **Cierre:** hash verificable + custodia iniciada (criterio cumplido).

### Escena 5 — CU-O16 Visualizar mapa de calor criminal (6:45–8:00)
- **Narración:** "La analítica criminal muestra la concentración delictiva en un mapa de calor legible."
- **Acción en app:** aplicar filtros (zona/tipo/fecha) → visualizar mapa.
- **Documento visible:** CU-O16.
- **Cierre:** visualización legible y proporcionada (RI-04).

### Escena 6 — CU-O36 Generar reporte operativo (8:00–9:15)
- **Narración:** "Generamos un reporte operativo con los datos del caso."
- **Acción en app:** seleccionar tipo y filtros → generar → revisar contenido.
- **Documento visible:** CU-O36.
- **Cierre:** contenido correcto y legible.

### Escena 7 — CU-O37 Exportar reporte PDF/Excel (9:15–10:30)
- **Narración:** "Exportamos el reporte a PDF/Excel; la exportación queda auditada."
- **Acción en app:** elegir formato → exportar → abrir archivo → mostrar registro de auditoría.
- **Documento visible:** CU-O37.
- **Cierre:** archivo legible + exportación auditada (RN-08).

### Escena 8 — Cierre (10:30–11:15)
- Resumen: 8 casos de uso demostrados, todos trazables a OE1–OE4.
- Mencionar que cada función mostrada cumplió su criterio de aceptación documentado.
- Mensaje final B2G: valor para instituciones gubernamentales + base para el negocio.

## Reglas del Video (obligatorias)

- Mostrar la app **en ejecución** y el **caso de uso documentado** al mismo tiempo.
- No mostrar gráficos miniatura, alargados o ilegibles (RI-04).
- No alterar el enfoque B2G ni los OE1–OE4 en la narración.
- Cada escena debe evidenciar el **criterio de aceptación** del CU.

## Checklist de Producción (resumen; ver `checklist-demostracion.md`)

- [ ] Entorno de demo listo con datos de prueba.
- [ ] Pantalla dividida configurada (app + documento).
- [ ] Verificada la legibilidad de textos y gráficos.
- [ ] Grabación con marcas de CU por escena.

## Pendientes por Confirmar

- **PC-V3:** Duración final exacta y si se requiere voz en off profesional o narración propia.
- **PC-V4:** Idioma de subtítulos y branding (logo/intro) a incluir.
