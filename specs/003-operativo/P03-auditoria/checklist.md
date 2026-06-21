# Checklist de Validación — P03 Auditoría y Trazabilidad (AMPLIACIÓN)

> **CASOS DE USO NUEVOS — NIVEL AUDITORÍA.** Lista de verificación de la especificación y de los
> criterios de aceptación. En esta fase se valida la **documentación**; las casillas de
> implementación quedan pendientes hasta la aprobación.

## A. Validación de la especificación (documental)
- [x] Diagnóstico de auditoría actual incluido (stack, cobertura, vacíos, integridad).
- [x] CU existentes (CU-O11…CU-O15) conservados, sin cambio de código, marcados como ampliados.
- [x] 16 CU nuevos (CU-O61…CU-O76) definidos con estructura completa de 18 puntos.
- [x] Arquitectura propuesta (middleware + decorador + servicio + async + integridad).
- [x] Modelo de datos (12 tablas de auditoría) documentado.
- [x] Plan por etapas sin eliminar funcionalidades.
- [x] Lista de tareas trazable a CU.
- [x] Riesgos y pendientes por confirmar (PC-A1…PC-A6).
- [x] Reglas de seguridad (FASE 6) y criterios de aceptación (FASE 11) adoptados.
- [x] Historias de usuario HU-O-61…HU-O-76 agregadas.
- [x] Matriz de trazabilidad actualizada (CU ↔ RF ↔ paquete ↔ HU ↔ tarea).
- [x] Documento UML actualizado (P03, modelo de datos, casos de uso nuevos).

## B. Criterios de aceptación generales (FASE 11) — a verificar en implementación
- [ ] 1. Toda operación sensible genera un evento.
- [ ] 2. Se identifica usuario, rol e institución.
- [ ] 3. Se identifica el registro afectado.
- [ ] 4. En actualizaciones se muestra valor anterior y nuevo.
- [ ] 5. En eliminaciones se conserva evidencia histórica.
- [ ] 6. Se registra inicio, última actividad, cierre y duración de sesión.
- [ ] 7. Los accesos denegados quedan registrados.
- [ ] 8. Las exportaciones quedan registradas.
- [ ] 9. Los eventos son inmutables.
- [ ] 10. Cualquier manipulación es detectable.
- [ ] 11. Se respeta aislamiento multi-tenant.
- [ ] 12. Los datos sensibles aparecen enmascarados.
- [ ] 13. Los auditores pueden reconstruir una operación completa.
- [ ] 14. Filtros por usuario, rol, sesión, módulo, caso de uso, entidad, fecha e IP.
- [ ] 15. La interfaz es clara, legible y funcional.

## C. Reglas de integridad (FASE 6) — a verificar en implementación
- [ ] Logs append-only; ningún rol (ni admin) altera el historial.
- [ ] Solo Auditor/Compliance consulta auditoría completa, respetando tenant.
- [ ] Marcas de tiempo en servidor, almacenadas en UTC.
- [ ] Hash por evento + encadenamiento `previous_hash`.
- [ ] Exportaciones auditadas; archivado sin perder integridad.
- [ ] No se almacenan contraseñas, tokens, claves ni API keys completas.
- [ ] Enmascaramiento de datos sensibles en antes/después y errores.
- [ ] Retención configurable por institución; conservación legal de eventos críticos.
- [ ] Toda alerta y revisión deja trazabilidad.

## D. Pruebas (FASE 10) — a ejecutar
- [ ] INSERT/UPDATE/DELETE, antes/después, usuario/rol, sesión y duración.
- [ ] Acceso denegado, exportación, alertas.
- [ ] Integridad por hash, detección de manipulación, cadena de custodia.
- [ ] Aislamiento por tenant, enmascaramiento.
- [ ] Rendimiento con gran volumen, paginación/filtros, recuperación ante fallos.
