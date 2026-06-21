"""
Reporte operativo consolidado (P08) — resumen estadístico en PDF.

Toma el payload del Dashboard (KPIs, delitos por tipo, indicadores operativos) y
genera un PDF profesional para distribución por correo (CU-O40) o programada (CU-O38).
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
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

BRAND = colors.HexColor("#4f46e5")
DARK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")


def _s(value: Any, default: str = "—") -> str:
    if value is None:
        return default
    t = str(value).strip()
    return t if t else default


def build_operational_report_pdf(*, generado_por: str = "Sistema") -> bytes:
    """Genera el PDF del reporte operativo consolidado desde el Dashboard."""
    from packages.dashboard_analitica.services.dashboard_service import DashboardService

    svc = DashboardService()
    overview = svc.overview()
    totals = overview.get("totals") or {}
    by_type = overview.get("crimes_by_type") or []
    op = overview.get("operational_indicators") or {}
    tasa = op.get("tasa_resolucion") or {}
    trend = op.get("tendencias_delictivas") or []

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2 * cm,
        title="Reporte operativo CrimeTrack",
    )

    styles = getSampleStyleSheet()
    h_title = ParagraphStyle(
        "h_title", parent=styles["Title"], textColor=DARK, fontSize=18, spaceAfter=2
    )
    h_sub = ParagraphStyle(
        "h_sub", parent=styles["Normal"], textColor=MUTED, fontSize=9, alignment=TA_CENTER
    )
    h_section = ParagraphStyle(
        "h_section", parent=styles["Heading2"], textColor=BRAND, fontSize=12, spaceBefore=14
    )
    cell = ParagraphStyle("cell", parent=styles["Normal"], fontSize=9, textColor=DARK)

    story: list[Any] = []
    story.append(Paragraph("CrimeTrack Analytics Corp", h_title))
    story.append(Paragraph("Reporte operativo consolidado", h_sub))
    generado = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(f"Generado por {_s(generado_por)} · {generado}", h_sub))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND))

    # ── KPIs ──
    story.append(Paragraph("Indicadores clave", h_section))
    kpi_rows = [
        ["Hechos registrados", _s(totals.get("fact_crimes"))],
        ["Casos totales", _s(tasa.get("total_casos"))],
        ["Casos resueltos", _s(tasa.get("casos_resueltos"))],
        ["Tasa de resolución", f"{_s(tasa.get('porcentaje'))}%"],
    ]
    kt = Table([[Paragraph(k, cell), Paragraph(str(v), cell)] for k, v in kpi_rows], colWidths=[8 * cm, 8 * cm])
    kt.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(kt)

    # ── Delitos por tipo ──
    story.append(Paragraph("Delitos por tipo (Top 10)", h_section))
    if by_type:
        data = [[Paragraph("<b>Tipo de delito</b>", cell), Paragraph("<b>Total</b>", cell)]]
        for item in by_type[:10]:
            data.append([Paragraph(_s(item.get("label")), cell), Paragraph(_s(item.get("value")), cell)])
        tt = Table(data, colWidths=[12 * cm, 4 * cm])
        tt.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("BACKGROUND", (0, 0), (-1, 0), BRAND),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(tt)
    else:
        story.append(Paragraph("Sin datos de delitos por tipo.", cell))

    # ── Tendencia anual ──
    story.append(Paragraph("Tendencia anual de hechos", h_section))
    if trend:
        data = [[Paragraph("<b>Año</b>", cell), Paragraph("<b>Hechos</b>", cell)]]
        for item in trend[-10:]:
            data.append([Paragraph(_s(item.get("label")), cell), Paragraph(_s(item.get("value")), cell)])
        tr = Table(data, colWidths=[8 * cm, 8 * cm])
        tr.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("BACKGROUND", (0, 0), (-1, 0), DARK),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(tr)
    else:
        story.append(Paragraph("Sin datos de tendencia.", cell))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(
        Paragraph(
            "Documento generado automáticamente por CrimeTrack Analytics Corp. "
            "Uso institucional reservado.",
            h_sub,
        )
    )

    doc.build(story)
    return buffer.getvalue()
