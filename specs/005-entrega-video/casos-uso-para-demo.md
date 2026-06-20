# Casos de Uso para Demostración en Video — CrimeTrack Analytics Corp

> Subconjunto de casos de uso a demostrar con la aplicación **en ejecución**, mostrando
> **simultáneamente** el caso de uso pertinente documentado (split-screen: app + documento).
> Subordinado a `004-uml-documentacion/casos-uso.md`.

## Lista Obligatoria (orden sugerido)

| # | CU | Nombre | Paquete | OE | Documento a mostrar en pantalla |
|---|---|---|---|---|---|
| 1 | CU-O01 | Iniciar sesión | P01 | habilitador (OT5) | `004/casos-uso.md` › CU-O01 |
| 2 | CU-O21 | Crear expediente criminal | P05 | OE4 | `004/casos-uso.md` › CU-O21 |
| 3 | CU-O31 | Registrar víctima | P07 | OE4 | `004/casos-uso.md` › CU-O31 |
| 4 | CU-O32 | Registrar sospechoso | P07 | OE4 | `004/casos-uso.md` › CU-O32 |
| 5 | CU-O26 | Registrar evidencia digital | P06 | OE4 | `004/casos-uso.md` › CU-O26 (+ CU-O27/CU-O28) |
| 6 | CU-O16 | Visualizar mapa de calor criminal | P04 | OE4 | `004/casos-uso.md` › CU-O16 |
| 7 | CU-O36 | Generar reporte operativo | P08 | OE4 | `004/casos-uso.md` › CU-O36 |
| 8 | CU-O37 | Exportar reporte PDF/Excel | P08 | OE4 | `004/casos-uso.md` › CU-O37 |

## Ficha de Demostración por Caso de Uso

> Cada ficha resume lo mínimo a mostrar. El criterio de aceptación debe verse cumplido en vivo.

### 1) CU-O01 — Iniciar sesión
- **Actor:** Usuario Institucional. **Dato a mostrar:** login + MFA.
- **Evidencia en vivo:** sesión creada y registro en bitácora (CU-O11).
- **Criterio:** Dado un usuario válido, Cuando inicia con MFA, Entonces obtiene sesión y queda registrado.

### 2) CU-O21 — Crear expediente criminal
- **Actor:** Investigador. **Dato a mostrar:** alta de expediente con folio único.
- **Evidencia en vivo:** estado inicial y auditoría.
- **Criterio:** se genera con folio único, estado inicial y registro de auditoría.

### 3) CU-O31 — Registrar víctima
- **Actor:** Investigador. **Dato a mostrar:** alta de víctima con protección de datos.
- **Evidencia en vivo:** vinculación al expediente del paso 2.
- **Criterio:** queda almacenada con protección y vinculable.

### 4) CU-O32 — Registrar sospechoso
- **Actor:** Investigador. **Dato a mostrar:** alta de sospechoso.
- **Evidencia en vivo:** vínculo al expediente (CU-O34).
- **Criterio:** queda almacenado y vinculable a un expediente.

### 5) CU-O26 — Registrar evidencia digital (+ carga + hash)
- **Actor:** Custodio. **Dato a mostrar:** registro de evidencia, carga de archivo (CU-O27) y hash (CU-O28).
- **Evidencia en vivo:** inicio de cadena de custodia y hash calculado.
- **Criterio:** evidencia con metadatos, archivo cifrado y hash verificable.

### 6) CU-O16 — Visualizar mapa de calor criminal
- **Actor:** Analista Criminal. **Dato a mostrar:** mapa con filtros (zona/tipo/fecha).
- **Evidencia en vivo:** visualización **legible y proporcionada** (RI-04).
- **Criterio:** mapa de calor legible según filtros.

### 7) CU-O36 — Generar reporte operativo
- **Actor:** Investigador/Usuario. **Dato a mostrar:** generación con filtros.
- **Evidencia en vivo:** contenido correcto del reporte.
- **Criterio:** contenido correcto y legible.

### 8) CU-O37 — Exportar reporte PDF/Excel
- **Actor:** Investigador/Usuario. **Dato a mostrar:** exportación y archivo resultante.
- **Evidencia en vivo:** archivo legible + registro de auditoría de la exportación.
- **Criterio:** archivo legible, completo y exportación auditada (RN-08).

## Trazabilidad de la Demo

| CU | HU | Paquete | OE | Criterio (en `casos-uso.md`) |
|---|---|---|---|---|
| CU-O01 | HU-O-01 | P01 | OT5 | ✔ |
| CU-O21 | HU-O-21 | P05 | OE4 | ✔ |
| CU-O31 | HU-O-31 | P07 | OE4 | ✔ |
| CU-O32 | HU-O-32 | P07 | OE4 | ✔ |
| CU-O26 | HU-O-26 | P06 | OE4 | ✔ |
| CU-O16 | HU-O-16 | P04 | OE4 | ✔ |
| CU-O36 | HU-O-36 | P08 | OE4 | ✔ |
| CU-O37 | HU-O-37 | P08 | OE4 | ✔ |

## Pendientes por Confirmar

- **PC-V1:** Datos de prueba (expediente/evidencia ficticios) para la grabación.
- **PC-V2:** Entorno de demostración (local o nube) y credenciales de demo.
