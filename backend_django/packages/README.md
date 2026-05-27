# Paquetes CrimeTrack (arquitectura por casos de uso)

Carpeta raíz de módulos alineados con los diagramas de paquetes del ingeniero.

| Paquete | Carpeta | Estado |
|---------|---------|--------|
| Autenticación y Seguridad | `autenticacion_seguridad/` | **Implementado** |
| Administración del Sistema | `administracion_sistema/` | Estructura lista |
| Auditoría y Trazabilidad | `auditoria_trazabilidad/` | Estructura lista |
| Dashboard y Analítica Criminal | `dashboard_analitica/` | Estructura lista |
| Gestión de Evidencias Digitales | `evidencias_digitales/` | Estructura lista |
| Gestión de Expedientes Criminales | `expedientes_criminales/` | Estructura lista |
| Gestión de Involucrados | `involucrados/` | Estructura lista |
| Reportería y Exportación | `reporteria_exportacion/` | Estructura lista |
| Asignación y Seguimiento de Investigaciones | `asignacion_investigaciones/` | Estructura lista |

## Tablas transaccionales (MinIO Parquet)

Prefijo: `datasets/transactional/`

- `app_roles`, `app_usuarios`, `app_involucrados`
- `app_caso_involucrado`, `app_evidencias`, `app_audit_logs`

Semilla inicial:

```bash
python manage.py seed_auth_minio
```
