"""
Registro central de paquetes del sistema (diagramas UML por paquete).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class PackageMeta:
    id: str
    nombre: str
    carpeta: str
    descripcion: str
    implementado: bool
    url_prefix: str | None = None


PACKAGE_REGISTRY: tuple[PackageMeta, ...] = (
    PackageMeta(
        id="autenticacion_seguridad",
        nombre="Autenticación y Seguridad",
        carpeta="autenticacion_seguridad",
        descripcion="RBAC, login, sesiones JWT, usuarios y roles.",
        implementado=True,
        url_prefix="auth",
    ),
    PackageMeta(
        id="administracion_sistema",
        nombre="Administración del Sistema",
        carpeta="administracion_sistema",
        descripcion="Usuarios, permisos, políticas, respaldos, catálogos, zonas y estado.",
        implementado=True,
        url_prefix="administracion",
    ),
    PackageMeta(
        id="auditoria_trazabilidad",
        nombre="Auditoría y Trazabilidad",
        carpeta="auditoria_trazabilidad",
        descripcion="Tablero, consulta, filtros y exportación de eventos de auditoría.",
        implementado=True,
        url_prefix="auditoria",
    ),
    PackageMeta(
        id="dashboard_analitica",
        nombre="Dashboard y Analítica Criminal",
        carpeta="dashboard_analitica",
        descripcion="KPIs, DuckDB, gráficos ejecutivos, filtros y analítica.",
        implementado=True,
        url_prefix="dashboard-analitica",
    ),
    PackageMeta(
        id="evidencias_digitales",
        nombre="Gestión de Evidencias Digitales",
        carpeta="evidencias_digitales",
        descripcion="Custodia de archivos en MinIO S3.",
        implementado=False,
    ),
    PackageMeta(
        id="expedientes_criminales",
        nombre="Gestión de Expedientes Criminales",
        carpeta="expedientes_criminales",
        descripcion="Expedientes y casos operativos.",
        implementado=True,
    ),
    PackageMeta(
        id="involucrados",
        nombre="Gestión de Involucrados",
        carpeta="involucrados",
        descripcion="Víctimas, sospechosos y testigos.",
        implementado=False,
    ),
    PackageMeta(
        id="reporteria_exportacion",
        nombre="Reportería y Exportación",
        carpeta="reporteria_exportacion",
        descripcion="Reportes y exportación de datasets.",
        implementado=False,
    ),
    PackageMeta(
        id="asignacion_investigaciones",
        nombre="Asignación y Seguimiento de Investigaciones",
        carpeta="asignacion_investigaciones",
        descripcion="Asignación de casos a investigadores.",
        implementado=True,
    ),
)


def list_packages() -> list[dict]:
    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "carpeta": p.carpeta,
            "descripcion": p.descripcion,
            "implementado": p.implementado,
            "url_prefix": p.url_prefix,
        }
        for p in PACKAGE_REGISTRY
    ]
