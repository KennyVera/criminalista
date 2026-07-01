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
        descripcion="Carga a MinIO S3, hash SHA-256 de integridad y cadena de custodia.",
        implementado=True,
        url_prefix="evidencias",
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
        descripcion="Generación de reportes PDF, envío por correo y programación recurrente.",
        implementado=True,
        url_prefix="reporteria",
    ),
    PackageMeta(
        id="asignacion_investigaciones",
        nombre="Asignación y Seguimiento de Investigaciones",
        carpeta="asignacion_investigaciones",
        descripcion="Asignación de casos a investigadores; patrullas y despacho (CU-O77/CU-O78).",
        implementado=True,
    ),
    PackageMeta(
        id="estructura_policial",
        nombre="Estructura Policial",
        carpeta="estructura_policial",
        descripcion="Departamentos, distritos, estaciones, rangos y personal policial operativo.",
        implementado=True,
        url_prefix="estructura-policial",
    ),
    PackageMeta(
        id="gestion_comercial_b2g",
        nombre="Gestión Comercial B2G y Clientes Institucionales",
        carpeta="gestion_comercial_b2g",
        descripcion="Leads, oportunidades, demos, licitaciones y propuestas B2G.",
        implementado=False,
    ),
    PackageMeta(
        id="ecosistema_apis",
        nombre="Ecosistema de APIs, Integraciones y Marketplace",
        carpeta="ecosistema_apis",
        descripcion="API keys, documentación, webhooks, consumo y conectores externos.",
        implementado=False,
    ),
    PackageMeta(
        id="gestion_cloud_sla",
        nombre="Gestión Cloud, SLA y Continuidad Operativa",
        carpeta="gestion_cloud_sla",
        descripcion="Uptime, backups, escalamiento, incidentes SLA y recuperación.",
        implementado=False,
    ),
    PackageMeta(
        id="gobierno_datos_bi",
        nombre="Gobierno de Datos e Inteligencia de Negocio Corporativa",
        carpeta="gobierno_datos_bi",
        descripcion="Consolidación, KPIs corporativos, benchmark y forecast B2G.",
        implementado=False,
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
