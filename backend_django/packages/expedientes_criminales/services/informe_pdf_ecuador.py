"""
Informe de investigación penal — formato profesional (Ecuador / PNEC contexto académico).

Estructura alineada a práctica policial ecuatoriana:
  encabezado institucional, identificación del hecho, involucrados,
  evidencias (cadena de custodia), actuaciones/bitácora, conclusiones y firmas.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from packages.expedientes_criminales.services.expediente_service import ExpedienteService


def _s(text: Any, default: str = "—") -> str:
    if text is None:
        return default
    t = str(text).strip()
    return t if t else default


def _fmt_size(size_bytes: Any) -> str:
    try:
        n = int(size_bytes)
    except (TypeError, ValueError):
        return "—"
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def build_informe_pdf(case_number: str, *, user: dict[str, Any] | None = None) -> bytes:
    svc = ExpedienteService()
    cn = str(case_number).strip()
    cabecera = svc.get_cabecera(cn)
    detalles = svc.detalles_generales(cn)
    involucrados = svc.list_involucrados(cn)
    evidencias = svc.list_evidencias(cn)
    bitacora = svc.list_bitacora(cn)

    resumen = detalles.get("resumen") or {}
    hechos = detalles.get("hechos") or []
    asig = cabecera.get("asignacion") or {}
    dim = cabecera.get("dim_caso") or {}

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2 * cm,
        title=f"Informe investigación {cn}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleEC",
        parent=styles["Heading1"],
        fontSize=13,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.HexColor("#1e3a5f"),
    )
    subtitle_style = ParagraphStyle(
        "SubtitleEC",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=4,
        textColor=colors.HexColor("#334155"),
    )
    section_style = ParagraphStyle(
        "SectionEC",
        parent=styles["Heading2"],
        fontSize=11,
        spaceBefore=10,
        spaceAfter=6,
        textColor=colors.HexColor("#0f172a"),
    )
    body_style = ParagraphStyle(
        "BodyEC",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        alignment=TA_JUSTIFY,
    )
    small_style = ParagraphStyle(
        "SmallEC",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#475569"),
    )

    now = datetime.now()
    elaborado = "—"
    if user:
        elaborado = f"{user.get('apellidos', '')} {user.get('nombres', '')}".strip() or _s(
            user.get("email")
        )

    story: list = []

    story.append(Paragraph("POLICÍA NACIONAL DEL ECUADOR", title_style))
    story.append(Paragraph("UNIDAD DE INVESTIGACIÓN CRIMINAL", subtitle_style))
    story.append(Paragraph("CrimeTrack Analytics Corp — Sistema de Gestión Investigativa", small_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("<b>INFORME DE INVESTIGACIÓN PENAL</b>", title_style))
    story.append(
        Paragraph(
            f"Lugar: Quito, Ecuador &nbsp;&nbsp;|&nbsp;&nbsp; Fecha: {now.strftime('%d/%m/%Y %H:%M')}",
            small_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e3a5f")))
    story.append(Spacer(1, 0.4 * cm))

    # I. DATOS GENERALES
    story.append(Paragraph("I. DATOS GENERALES DEL EXPEDIENTE", section_style))
    datos = [
        ["N.º de caso / expediente", _s(cn)],
        ["Estado procesal", _s(cabecera.get("estado_caso") or dim.get("estado_caso"))],
        ["Prioridad", _s(dim.get("prioridad_caso"))],
        ["Fecha de reporte", _s(dim.get("fecha_reporte"))],
        ["Avance investigativo", f"{cabecera.get('avance_pct', 0)}%"],
        ["Detective asignado", _s(asig.get("detective_nombre") or dim.get("investigador_asignado"))],
        ["Fecha asignación", _s(asig.get("fecha_asignacion") or dim.get("fecha_asignacion"))],
        ["Tipo de informe", "Informe de avance y estado de investigación"],
    ]
    t_datos = Table(datos, colWidths=[5.5 * cm, 11 * cm])
    t_datos.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_datos)

    # II. HECHO DELICTIVO
    story.append(Paragraph("II. IDENTIFICACIÓN DEL HECHO DELICTIVO", section_style))
    hecho_rows = [
        ["Tipo de delito", _s(resumen.get("primary_type"))],
        ["Descripción / modalidad", _s(resumen.get("description"))],
        ["Código IUCR / FBI", f"{_s(resumen.get('iucr'))} / {_s(resumen.get('fbi_code'))}"],
        ["Fecha y hora del hecho", _s(resumen.get("date"))],
        ["Distrito policial", _s(resumen.get("district"))],
        ["Sector / beat", _s(resumen.get("beat"))],
        ["Lugar / referencia", _s(resumen.get("block"))],
        ["Descripción del lugar", _s(resumen.get("location_description"))],
        ["Coordenadas", f"{_s(resumen.get('latitude'))}, {_s(resumen.get('longitude'))}"],
        ["¿Detención?", _s(resumen.get("arrest"))],
        ["¿Violencia doméstica?", _s(resumen.get("domestic"))],
        ["Registros en Data Lake", str(len(hechos) or resumen.get("total_registros_lake") or 0)],
    ]
    t_hecho = Table(hecho_rows, colWidths=[5.5 * cm, 11 * cm])
    t_hecho.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_hecho)

    narrativa = (
        f"En el sector {_s(resumen.get('block'))}, distrito {_s(resumen.get('district'))}, "
        f"se registró un hecho tipificado como {_s(resumen.get('primary_type'))}, "
        f"con modalidad {_s(resumen.get('description'))}, ocurrido en fecha {_s(resumen.get('date'))}. "
        f"El caso {_s(cn)} se encuentra bajo seguimiento conforme al Código Orgánico Integral Penal (COIP) "
        f"y protocolos de la Policía Nacional del Ecuador."
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(narrativa, body_style))

    # III. INVOLUCRADOS
    story.append(Paragraph("III. PERSONAS INVOLUCRADAS", section_style))
    if involucrados:
        inv_header = ["Tipo", "Nombres y apellidos", "Identificación", "Declaración / notas"]
        inv_data = [inv_header]
        for inv in involucrados:
            inv_data.append(
                [
                    _s(inv.get("tipo_relacion")),
                    f"{_s(inv.get('nombres'))} {_s(inv.get('apellidos'))}",
                    _s(inv.get("identificacion")),
                    _s(inv.get("declaracion"), "")[:120] or "—",
                ]
            )
        t_inv = Table(inv_data, colWidths=[2.5 * cm, 4.5 * cm, 3 * cm, 6.5 * cm])
        t_inv.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(t_inv)
    else:
        story.append(Paragraph("No constan personas involucradas registradas en el expediente.", body_style))

    # IV. EVIDENCIAS
    story.append(Paragraph("IV. EVIDENCIAS Y CADENA DE CUSTODIA", section_style))
    if evidencias:
        ev_header = ["Tipo", "Archivo", "Tamaño", "Custodio", "Fecha registro", "Referencia MinIO"]
        ev_data = [ev_header]
        for ev in evidencias:
            ev_data.append(
                [
                    _s(ev.get("tipo_evidencia")),
                    _s(ev.get("nombre_archivo") or ev.get("tipo_evidencia")),
                    _fmt_size(ev.get("peso_bytes") or ev.get("peso_mb")),
                    _s(ev.get("custodio_nombre") or ev.get("fk_usuario_carga")),
                    _s(ev.get("fecha_registro") or ev.get("fecha_subida"))[:19],
                    _s(ev.get("minio_url"), "")[:45] + ("…" if ev.get("minio_url") else ""),
                ]
            )
        t_ev = Table(ev_data, colWidths=[2.2 * cm, 3 * cm, 1.5 * cm, 3 * cm, 2.8 * cm, 3.5 * cm])
        t_ev.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(t_ev)
        story.append(Spacer(1, 0.15 * cm))
        story.append(
            Paragraph(
                "Nota: Los archivos digitales se conservan en repositorio MinIO con trazabilidad "
                "de custodia. Para visualización ampliada, consulte el expediente digital.",
                small_style,
            )
        )
    else:
        story.append(Paragraph("No constan evidencias digitales adjuntas al expediente.", body_style))

    # V. BITÁCORA
    story.append(Paragraph("V. ACTUACIONES Y BITÁCORA DE INVESTIGACIÓN", section_style))
    if bitacora:
        for entry in bitacora[:15]:
            line = (
                f"<b>{_s(entry.get('fecha_hora'))[:19]}</b> — "
                f"{_s(entry.get('autor_nombre'))} "
                f"(Avance {entry.get('avance_pct', 0)}%, estado: {_s(entry.get('estado_caso'))})<br/>"
                f"{_s(entry.get('nota'))}"
            )
            story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 0.15 * cm))
    else:
        story.append(
            Paragraph(
                "Sin entradas en bitácora. Se recomienda documentar diligencias conforme "
                "al artículo 178 COIP (investigación preparatoria).",
                body_style,
            )
        )

    # VI. CONCLUSIONES
    story.append(Paragraph("VI. CONCLUSIONES Y RECOMENDACIONES", section_style))
    avance = int(cabecera.get("avance_pct") or 0)
    estado = _s(cabecera.get("estado_caso") or dim.get("estado_caso"))
    conclusion = (
        f"El expediente <b>{cn}</b> se encuentra en estado <b>{estado}</b> con un avance del "
        f"<b>{avance}%</b>. Se han registrado {len(involucrados)} persona(s) involucrada(s) y "
        f"{len(evidencias)} evidencia(s) digital(es). "
        "Se recomienda continuar con las diligencias de investigación, preservar la cadena de custodia "
        "y remitir al fiscalía competente cuando existan elementos suficientes, conforme al COIP."
    )
    story.append(Paragraph(conclusion, body_style))

    # VII. FIRMAS
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph("VII. FIRMAS DE RESPONSABILIDAD", section_style))
    firmas = [
        ["Elaborado por", elaborado, now.strftime("%d/%m/%Y")],
        ["Detective a cargo", _s(asig.get("detective_nombre")), "________________"],
        ["Revisado por (Comisario)", "________________________", "________________"],
        ["Vo. Bo. Unidad de Investigación", "________________________", "________________"],
    ]
    t_fir = Table(firmas, colWidths=[5 * cm, 6.5 * cm, 5 * cm])
    t_fir.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(t_fir)
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            f"Documento generado electrónicamente por CrimeTrack — Folio {cn}-{now.strftime('%Y%m%d%H%M')}. "
            "Uso institucional. Art. 5 COIP — debido proceso.",
            small_style,
        )
    )

    doc.build(story)
    return buffer.getvalue()
