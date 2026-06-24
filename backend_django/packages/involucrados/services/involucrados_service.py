"""
Servicio del paquete Gestión de Involucrados (P07).

Implementa el perfil completo del involucrado:
- Consultar perfil de involucrado (datos personales + foto).
- Ver historial criminal (casos en los que figura, con su rol).
- Consultar expedientes relacionados.
- Editar involucrado (con validación de identificación).
- Buscar involucrado.
- Registrar / consultar foto de perfil en MinIO.
"""

from __future__ import annotations

import mimetypes
import os
import uuid
from datetime import date, datetime
from typing import Any

import pandas as pd

from core.services.minio_store import MinioParquetStore
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

# Campos de perfil que se incorporan a app_involucrados además de los originales.
PERFIL_COLS = (
    "alias",
    "genero",
    "nacionalidad",
    "telefono",
    "direccion",
    "estado_civil",
    "ocupacion",
    "observaciones",
    "foto_url",
    "fecha_registro",
    "fk_usuario_registro",
    "actualizado_en",
)

# Campos editables del perfil (texto).
EDITABLE_COLS = (
    "nombres",
    "apellidos",
    "identificacion",
    "fecha_nacimiento",
    "antecedentes",
    "alias",
    "genero",
    "nacionalidad",
    "telefono",
    "direccion",
    "estado_civil",
    "ocupacion",
    "observaciones",
)

GENEROS = ("", "Masculino", "Femenino", "Otro", "No especificado")


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _calc_edad(fecha_nacimiento: Any) -> int | None:
    if not fecha_nacimiento:
        return None
    raw = str(fecha_nacimiento).strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            nac = datetime.strptime(raw[: len(fmt) + 2], fmt).date()
            break
        except ValueError:
            nac = None
    else:
        nac = None
    if nac is None:
        try:
            nac = datetime.fromisoformat(raw).date()
        except ValueError:
            return None
    today = date.today()
    edad = today.year - nac.year - ((today.month, today.day) < (nac.month, nac.day))
    return edad if 0 <= edad <= 130 else None


class InvolucradosService:
    def __init__(self) -> None:
        self.tx = TransactionalMinioStore()
        self.olap = MinioParquetStore()
        self.tx.ensure_tables()
        self._bucket = os.getenv("MINIO_BUCKET", "crimetrack-evidence")
        self._prefix = os.getenv("MINIO_INVOLUCRADOS_PREFIX", "involucrados")

    # ── Helpers ──
    def _inv_df(self) -> pd.DataFrame:
        df = self.tx.read_table("app_involucrados")
        for col in PERFIL_COLS:
            if col not in df.columns:
                df[col] = ""
        return df

    @staticmethod
    def validar_identificacion(identificacion: str) -> str:
        ident = str(identificacion or "").strip()
        if not ident:
            return ""
        if len(ident) < 4:
            raise ValueError("La identificación debe tener al menos 4 caracteres.")
        if len(ident) > 30:
            raise ValueError("La identificación no puede superar 30 caracteres.")
        if not all(c.isalnum() or c in ".-" for c in ident):
            raise ValueError(
                "La identificación solo admite letras, números, punto y guion."
            )
        return ident

    def _get_row(self, id_involucrado: int) -> tuple[pd.DataFrame, pd.Series]:
        df = self._inv_df()
        if df.empty:
            raise ValueError("Involucrado no encontrado")
        mask = df["id_involucrado"].astype("Int64") == int(id_involucrado)
        if not mask.any():
            raise ValueError("Involucrado no encontrado")
        return df, mask

    # ── Perfil ──
    def get_basico(self, id_involucrado: int) -> dict[str, Any] | None:
        df = self._inv_df()
        if df.empty:
            return None
        mask = df["id_involucrado"].astype("Int64") == int(id_involucrado)
        if not mask.any():
            return None
        row = _json_safe(df[mask].iloc[0].to_dict())
        row["edad"] = _calc_edad(row.get("fecha_nacimiento"))
        row["tiene_foto"] = bool(str(row.get("foto_url") or "").strip())
        return row

    def get_perfil(self, id_involucrado: int) -> dict[str, Any]:
        persona = self.get_basico(id_involucrado)
        if persona is None:
            raise ValueError("Involucrado no encontrado")

        historial = self._historial_criminal(int(id_involucrado))
        roles = [h["tipo_relacion"] for h in historial]
        stats = {
            "total_casos": len(historial),
            "como_victima": sum(1 for r in roles if r == "Víctima"),
            "como_sospechoso": sum(1 for r in roles if r == "Sospechoso"),
            "como_testigo": sum(1 for r in roles if r == "Testigo"),
            "abiertos": sum(1 for h in historial if h.get("activo")),
        }
        return {
            "involucrado": persona,
            "historial": historial,
            "expedientes_relacionados": historial,
            "estadisticas": stats,
        }

    def _historial_criminal(self, id_involucrado: int) -> list[dict[str, Any]]:
        rel_df = self.tx.read_table("app_caso_involucrado")
        if rel_df.empty:
            return []
        rels = rel_df[rel_df["fk_involucrado"].astype("Int64") == int(id_involucrado)]
        if rels.empty:
            return []

        exp_df = self.tx.read_table("app_expedientes")
        exp_by_caso: dict[int, dict[str, Any]] = {}
        if not exp_df.empty and "fk_caso" in exp_df.columns:
            for r in exp_df.to_dict(orient="records"):
                try:
                    exp_by_caso[int(r.get("fk_caso"))] = r
                except (TypeError, ValueError):
                    continue

        estados_abiertos = {
            "abierto",
            "en investigación",
            "en investigacion",
            "activo",
            "reabierto",
            "pendiente",
        }
        items: list[dict[str, Any]] = []
        for rel in rels.to_dict(orient="records"):
            try:
                fk_caso = int(rel.get("fk_caso"))
            except (TypeError, ValueError):
                continue
            exp = exp_by_caso.get(fk_caso)
            dim = None
            if not exp:
                try:
                    dim = self.olap.get_record("dim_caso", str(fk_caso))
                except Exception:
                    dim = None
            case_number = str(
                (exp or {}).get("case_number")
                or (dim or {}).get("case_number")
                or fk_caso
            )
            tipo_delito = (exp or {}).get("tipo_delito") or (dim or {}).get("primary_type") or "—"
            estado = (
                (exp or {}).get("estado")
                or (dim or {}).get("estado_caso")
                or "—"
            )
            fecha = (
                (exp or {}).get("fecha_hecho")
                or (dim or {}).get("fecha_reporte")
                or rel.get("fecha_asociacion")
            )
            items.append(
                _json_safe(
                    {
                        "id_relacion": int(rel.get("id_relacion")),
                        "fk_caso": fk_caso,
                        "case_number": case_number,
                        "tipo_relacion": rel.get("tipo_relacion"),
                        "declaracion": rel.get("declaracion"),
                        "fecha_asociacion": rel.get("fecha_asociacion"),
                        "tipo_delito": tipo_delito,
                        "estado": estado,
                        "fecha_hecho": fecha,
                        "es_expediente": bool(exp),
                        "activo": str(estado).strip().lower() in estados_abiertos,
                    }
                )
            )
        items.sort(key=lambda x: str(x.get("fecha_asociacion") or ""), reverse=True)
        return items

    # ── Edición ──
    def update(
        self, id_involucrado: int, *, data: dict[str, Any], user: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        df, mask = self._get_row(id_involucrado)
        antes = _json_safe(df[mask].iloc[0].to_dict())

        cambios: dict[str, Any] = {}
        for col in EDITABLE_COLS:
            if col not in data:
                continue
            valor = data.get(col)
            valor = "" if valor is None else str(valor).strip()
            if col == "identificacion":
                valor = self.validar_identificacion(valor)
            if str(antes.get(col) or "") != valor:
                cambios[col] = valor

        if not cambios:
            raise ValueError("No se detectaron cambios para actualizar.")

        for col, valor in cambios.items():
            df.loc[mask, col] = valor
        df.loc[mask, "actualizado_en"] = utc_now_iso()
        self.tx.write_table("app_involucrados", df)

        despues = _json_safe(df[mask].iloc[0].to_dict())
        return antes, despues

    # ── Foto de perfil ──
    def set_foto(
        self,
        id_involucrado: int,
        *,
        file_obj: Any,
        filename: str,
        user: dict[str, Any],
    ) -> dict[str, Any]:
        df, mask = self._get_row(id_involucrado)

        body = file_obj.read()
        if not body:
            raise ValueError("El archivo de imagen está vacío.")
        content_type = (
            getattr(file_obj, "content_type", None)
            or mimetypes.guess_type(filename)[0]
            or ""
        )
        if not str(content_type).startswith("image/"):
            raise ValueError("La foto de perfil debe ser una imagen.")

        safe_name = "".join(c for c in filename if c.isalnum() or c in "._-") or "foto"
        key = f"{self._prefix}/{int(id_involucrado)}/{uuid.uuid4().hex}_{safe_name}"
        self.olap._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body,
            ContentType=content_type or "application/octet-stream",
        )
        df.loc[mask, "foto_url"] = f"s3://{self._bucket}/{key}"
        df.loc[mask, "actualizado_en"] = utc_now_iso()
        self.tx.write_table("app_involucrados", df)
        return self.get_basico(id_involucrado)

    def get_foto(self, id_involucrado: int) -> dict[str, Any] | None:
        persona = self.get_basico(id_involucrado)
        if not persona:
            return None
        url = str(persona.get("foto_url") or "").strip()
        if not url:
            return None
        raw = url[len("s3://") :] if url.startswith("s3://") else url
        parts = raw.split("/", 1)
        if len(parts) != 2:
            return None
        bucket, key = parts
        resp = self.olap._client.get_object(Bucket=bucket, Key=key)
        body = resp["Body"].read()
        content_type = resp.get("ContentType") or "image/jpeg"
        return {"body": body, "content_type": content_type}

    # ── Búsqueda ──
    def search(self, q: str, *, limit: int = 20) -> list[dict[str, Any]]:
        df = self._inv_df()
        if df.empty:
            return []
        q_low = str(q or "").strip().lower()
        if q_low:
            def _match(row: pd.Series) -> bool:
                full = f"{row.get('nombres', '')} {row.get('apellidos', '')}".lower()
                ident = str(row.get("identificacion", "")).lower()
                alias = str(row.get("alias", "")).lower()
                return q_low in full or q_low in ident or q_low in alias

            df = df[df.apply(_match, axis=1)]
        df = df.head(int(limit))
        out = []
        for row in df.to_dict(orient="records"):
            r = _json_safe(row)
            r["edad"] = _calc_edad(r.get("fecha_nacimiento"))
            r["tiene_foto"] = bool(str(r.get("foto_url") or "").strip())
            out.append(r)
        return out
