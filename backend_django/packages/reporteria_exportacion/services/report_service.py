"""
Servicio de Reportería y Exportación (P08).

CU-O40 — Enviar reporte autorizado por correo (destinatarios definidos por el usuario).
CU-O38 — Programar reportes recurrentes (diaria / semanal / mensual) ejecutados por Celery.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from packages.administracion_sistema.storage import AdminMinioStore

TABLE = "sys_reportes_programados"
FRECUENCIAS = ("diaria", "semanal", "mensual")
TIPOS_REPORTE = {
    "operativo": "Reporte operativo consolidado",
    "expediente": "Informe de expediente",
}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return _now().isoformat()


def parse_recipients(raw: Any) -> list[str]:
    """Convierte una cadena (coma/; separada) o lista en una lista de correos válidos."""
    if isinstance(raw, (list, tuple)):
        items = [str(x) for x in raw]
    else:
        items = re.split(r"[,;\s]+", str(raw or ""))
    out: list[str] = []
    for it in items:
        e = it.strip()
        if e and _EMAIL_RE.match(e) and e not in out:
            out.append(e)
    return out


class ReportService:
    def __init__(self) -> None:
        self.admin = AdminMinioStore()

    # ── Generación de PDF ──────────────────────────────────────────────
    @staticmethod
    def build_pdf(tipo_reporte: str, *, case_number: str | None = None, generado_por: str = "Sistema") -> tuple[bytes, str]:
        """Devuelve (pdf_bytes, filename) según el tipo de reporte."""
        tipo = (tipo_reporte or "operativo").strip().lower()
        if tipo == "expediente":
            if not case_number:
                raise ValueError("Debe indicar el número de caso para el informe de expediente.")
            from packages.expedientes_criminales.services.informe_pdf_ecuador import build_informe_pdf

            pdf = build_informe_pdf(case_number, user=None)
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(case_number))
            return pdf, f"Informe_{safe}.pdf"

        from packages.reporteria_exportacion.services.report_pdf import build_operational_report_pdf

        pdf = build_operational_report_pdf(generado_por=generado_por)
        stamp = _now().strftime("%Y%m%d")
        return pdf, f"Reporte_Operativo_{stamp}.pdf"

    # ── Envío (CU-O40) ─────────────────────────────────────────────────
    def send_report(
        self,
        *,
        tipo_reporte: str,
        destinatarios: Any,
        case_number: str | None = None,
        generado_por: str = "Sistema",
        mensaje: str = "",
    ) -> dict[str, Any]:
        from packages.autenticacion_seguridad.services.email_service import send_report_email

        recipients = parse_recipients(destinatarios)
        if not recipients:
            raise ValueError("Debe indicar al menos un correo electrónico válido.")

        pdf_bytes, filename = self.build_pdf(
            tipo_reporte, case_number=case_number, generado_por=generado_por
        )
        nombre_tipo = TIPOS_REPORTE.get((tipo_reporte or "operativo").strip().lower(), "Reporte")
        subject = f"CrimeTrack — {nombre_tipo}"
        body = (
            f"Adjuntamos el {nombre_tipo.lower()} solicitado en CrimeTrack Analytics Corp.\n\n"
            f"{mensaje.strip() + chr(10) + chr(10) if mensaje.strip() else ''}"
            f"Generado por: {generado_por}\n"
            f"Fecha: {_now().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"— CrimeTrack Analytics Corp\n"
        )
        send_report_email(
            to_emails=recipients,
            subject=subject,
            body=body,
            pdf_bytes=pdf_bytes,
            filename=filename,
        )
        return {
            "enviado": True,
            "destinatarios": recipients,
            "archivo": filename,
            "tipo_reporte": tipo_reporte,
        }

    # ── Programación (CU-O38) ──────────────────────────────────────────
    def list_schedules(self) -> list[dict[str, Any]]:
        df = self.admin.read_table(TABLE)
        if df.empty:
            return []
        return df.sort_values("id").to_dict(orient="records")

    def create_schedule(
        self,
        *,
        nombre: str,
        tipo_reporte: str,
        destinatarios: Any,
        frecuencia: str,
        hora_programada: str,
        creado_por: str = "Sistema",
        activo: bool = True,
    ) -> dict[str, Any]:
        recipients = parse_recipients(destinatarios)
        if not recipients:
            raise ValueError("Debe indicar al menos un correo electrónico válido.")
        freq = (frecuencia or "").strip().lower()
        if freq not in FRECUENCIAS:
            raise ValueError(f"Frecuencia inválida. Use: {', '.join(FRECUENCIAS)}.")
        tipo = (tipo_reporte or "operativo").strip().lower()
        if tipo not in TIPOS_REPORTE:
            raise ValueError(f"Tipo de reporte inválido. Use: {', '.join(TIPOS_REPORTE)}.")
        hora = (hora_programada or "08:00").strip()
        if not re.match(r"^\d{1,2}:\d{2}$", hora):
            raise ValueError("La hora programada debe tener formato HH:MM.")

        return self.admin.append_row(
            TABLE,
            {
                "nombre": nombre.strip() or "Reporte programado",
                "tipo_reporte": tipo,
                "destinatarios": ", ".join(recipients),
                "frecuencia": freq,
                "hora_programada": hora,
                "activo": bool(activo),
                "creado_por": creado_por,
                "creado_en": utc_now_iso(),
                "ultima_ejecucion": "",
                "ultimo_estado": "",
            },
        )

    def update_schedule(self, schedule_id: int, updates: dict[str, Any]) -> dict[str, Any] | None:
        clean: dict[str, Any] = {}
        if "destinatarios" in updates:
            recipients = parse_recipients(updates["destinatarios"])
            if not recipients:
                raise ValueError("Debe indicar al menos un correo electrónico válido.")
            clean["destinatarios"] = ", ".join(recipients)
        for key in ("nombre", "tipo_reporte", "frecuencia", "hora_programada", "activo"):
            if key in updates:
                clean[key] = updates[key]
        if "activo" in clean:
            clean["activo"] = bool(clean["activo"])
        return self.admin.update_row(TABLE, int(schedule_id), clean)

    def delete_schedule(self, schedule_id: int) -> bool:
        return self.admin.delete_row(TABLE, int(schedule_id))

    @staticmethod
    def _is_active(cfg: dict[str, Any]) -> bool:
        val = cfg.get("activo")
        if isinstance(val, str):
            return val.strip().lower() in ("true", "1", "sí", "si", "yes")
        return bool(val)

    @staticmethod
    def _is_due(cfg: dict[str, Any], now: datetime) -> bool:
        hora = str(cfg.get("hora_programada") or "08:00")
        try:
            hh, mm = (int(x) for x in hora.split(":")[:2])
        except ValueError:
            hh, mm = 8, 0
        # Aún no llega la hora programada de hoy.
        if (now.hour, now.minute) < (hh, mm):
            return False
        last_raw = str(cfg.get("ultima_ejecucion") or "").strip()
        if not last_raw:
            return True
        try:
            last = datetime.fromisoformat(last_raw.replace("Z", "+00:00"))
        except ValueError:
            return True
        freq = str(cfg.get("frecuencia") or "diaria").lower()
        if freq == "diaria":
            return last.date() < now.date()
        if freq == "semanal":
            return (now.date() - last.date()).days >= 7
        if freq == "mensual":
            return (last.year, last.month) < (now.year, now.month)
        return last.date() < now.date()

    def run_due_scheduled(self) -> list[dict[str, Any]]:
        """Ejecuta los reportes programados vencidos (Celery beat / CU-O38)."""
        results: list[dict[str, Any]] = []
        now = _now()
        for cfg in self.list_schedules():
            if not self._is_active(cfg) or not self._is_due(cfg, now):
                continue
            sid = int(cfg["id"])
            try:
                res = self.send_report(
                    tipo_reporte=str(cfg.get("tipo_reporte") or "operativo"),
                    destinatarios=cfg.get("destinatarios"),
                    generado_por=f"Programación «{cfg.get('nombre')}»",
                    mensaje="Este es un reporte automático programado.",
                )
                self.admin.update_row(
                    TABLE,
                    sid,
                    {"ultima_ejecucion": utc_now_iso(), "ultimo_estado": "enviado"},
                )
                results.append({"id": sid, "estado": "enviado", **res})
            except Exception as exc:  # noqa: BLE001
                self.admin.update_row(
                    TABLE,
                    sid,
                    {"ultima_ejecucion": utc_now_iso(), "ultimo_estado": f"error: {exc}"},
                )
                results.append({"id": sid, "estado": "error", "error": str(exc)})
        return results
