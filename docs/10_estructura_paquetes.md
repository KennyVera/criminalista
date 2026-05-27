# Estructura por paquetes — CrimeTrack

## Carpeta raíz

`backend_django/packages/` — todos los módulos por caso de uso (diagramas en `Desktop/Diagramas de paquetes`).

## Paquetes

| # | Diagrama | Carpeta |
|---|----------|---------|
| 1 | Autenticación y Seguridad | `autenticacion_seguridad/` |
| 2 | Gestión de Expedientes Criminales | `expedientes_criminales/` |
| 3 | Asignación y Seguimiento de Investigaciones | `asignacion_investigaciones/` |
| 4 | Gestión de Involucrados | `involucrados/` |
| 5 | Gestión de Evidencias Digitales | `evidencias_digitales/` |
| 6 | Dashboard y Analítica Criminal | `dashboard_analitica/` |
| 7 | Reportería y Exportación | `reporteria_exportacion/` |
| 8 | Auditoría y Trazabilidad | `auditoria_trazabilidad/` |
| 9 | Administración del Sistema | `administracion_sistema/` |

## API del paquete Autenticación

| Método | Ruta |
|--------|------|
| POST | `/api/packages/autenticacion/login/` |
| POST | `/api/packages/autenticacion/logout/` |
| GET | `/api/packages/autenticacion/me/` |
| GET | `/api/packages/autenticacion/roles/` |
| GET | `/api/packages/` — índice de paquetes |

## MinIO — tablas transaccionales

Prefijo: `datasets/transactional/*.parquet`

Semilla:

```bash
python manage.py seed_auth_minio
```

## Usuario demo

| Campo | Valor |
|-------|--------|
| Email | `kennyvera43@gmail.com` |
| Contraseña | `CrimeTrack2026!` |
| Placa | `CPD-1001` |
| Rol | Admin |

## Sesiones activas (Admin)

- API: `GET /api/packages/autenticacion/sesiones-activas/`
- UI: menú **Seguridad → Sesiones activas** (`/seguridad/sesiones-activas`)
- Tabla MinIO: `app_sesiones_activas.parquet`

## Administración del Sistema (solo Admin)

Prefijo API: `/api/packages/administracion/`

| Caso de uso (diagrama) | Ruta UI | API |
|------------------------|---------|-----|
| Registrar usuarios (+ roles + permisos) | `/admin/usuarios` | `POST /usuarios/` |
| Editar / eliminar / activar-desactivar | `/admin/usuarios` | `PATCH`, `DELETE`, `PATCH .../estado/` |
| Gestionar permisos | `/admin/permisos` | `GET/PUT /roles/{id}/permisos/` |
| Políticas de seguridad | `/admin/politicas` | `GET/POST/PATCH politicas-seguridad/` |
| Parámetros del sistema | `/admin/parametros` | `GET/PATCH parametros/` |
| Configurar respaldos | `/admin/respaldos` | `GET/POST respaldos/` |
| Catálogos de delitos | `/admin/catalogos` | CRUD `catalogos-delitos/` |
| Zonas geográficas | `/admin/zonas` | CRUD `zonas-geograficas/` |
| Supervisar estado | `/admin/estado-sistema` | `GET estado-sistema/` |

Semilla MinIO admin:

```bash
python manage.py seed_admin_sistema
```

Tablas en `datasets/admin/*.parquet`.

## Recuperar contraseña

- `POST /api/packages/autenticacion/recuperar-contrasena/` — envía código por Gmail
- `POST /api/packages/autenticacion/restablecer-contrasena/` — `{ email, code, new_password }`
- UI: `/recuperar-contrasena` (enlace en login)
