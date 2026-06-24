from __future__ import annotations

import os
from datetime import date, datetime, timezone
from typing import Any

import pandas as pd

from core.services.minio_store import MinioParquetStore
from packages.expedientes_criminales.services.datalake_service import ExpedienteDatalakeService
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

TIPOS_INVOLUCRADO = ("Víctima", "Testigo", "Sospechoso")
ESTADOS_CASO = ("Abierto", "En investigación", "Resuelto", "Cerrado", "Archivado")
# RN-09: estados que implican cierre del expediente y exigen criterios de completitud.
ESTADOS_CIERRE = ("Cerrado", "Archivado")

# Ciclo de vida administrativo del expediente (independiente del avance investigativo).
ESTADOS_EXPEDIENTE = ("ACTIVO", "CERRADO", "ARCHIVADO", "REABIERTO", "ELIMINADO")
# Transiciones permitidas entre estados del expediente.
TRANSICIONES_EXPEDIENTE: dict[str, set[str]] = {
    "ACTIVO": {"CERRADO", "ELIMINADO"},
    "REABIERTO": {"CERRADO", "ELIMINADO"},
    "CERRADO": {"REABIERTO", "ARCHIVADO", "ELIMINADO"},
    "ARCHIVADO": {"ELIMINADO"},
    "ELIMINADO": set(),
}
# Estados en los que el expediente admite edición de sus datos.
ESTADOS_EDITABLES = ("ACTIVO", "REABIERTO")
PRIORIDADES_EXPEDIENTE = ("Alta", "Media", "Baja")
TIPOS_DELITO = (
    "Robo",
    "Hurto",
    "Homicidio",
    "Asesinato",
    "Violencia intrafamiliar",
    "Estafa",
    "Secuestro",
    "Narcotráfico",
    "Daño a la propiedad",
    "Lesiones",
    "Otro",
)


def _safe_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
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


def _parse_fecha_hecho(value: str) -> date:
    """Valida el formato y que la fecha del hecho no sea futura."""
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("La fecha del hecho es obligatoria.")
    # Acepta YYYY-MM-DD (input date) o ISO con hora.
    parsed: date | None = None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            parsed = datetime.strptime(raw[: len(fmt) + 2], fmt).date()
            break
        except ValueError:
            continue
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(raw).date()
        except ValueError as exc:
            raise ValueError("Formato de fecha inválido. Use el formato AAAA-MM-DD.") from exc
    hoy = datetime.now(timezone.utc).date()
    if parsed > hoy:
        raise ValueError(
            f"La fecha del hecho ({parsed.isoformat()}) no puede ser futura. "
            f"Hoy es {hoy.isoformat()}."
        )
    return parsed


def _avance_por_estado(estado: str) -> int:
    mapping = {
        "abierto": 15,
        "en investigación": 55,
        "cerrado": 90,
        "archivado": 100,
        "resuelto": 90,
        "importado": 15,
    }
    return mapping.get(str(estado or "").lower().strip(), 30)


class ExpedienteService:
    def __init__(self) -> None:
        self.tx = TransactionalMinioStore()
        self.datalake = ExpedienteDatalakeService()
        self.olap = MinioParquetStore()
        self.tx.ensure_tables()
        self._evidence_bucket = os.getenv("MINIO_BUCKET", "crimetrack-evidence")
        self._evidence_prefix = os.getenv("MINIO_EVIDENCE_PREFIX", "evidencias")

    def _normalize_case(self, case_number: str) -> str:
        return str(case_number).strip()

    def detective_has_active_assignment(self, fk_detective: int, case_number: str) -> bool:
        cn = self._normalize_case(case_number).upper()
        df = self.tx.read_table("app_asignaciones")
        if df.empty:
            return False
        mask = (
            (df["case_number"].astype(str).str.upper() == cn)
            & (df["fk_detective"].astype(int) == fk_detective)
            & (df["estado_asignacion"].astype(str) == "Activa")
        )
        return bool(mask.any())

    def get_cabecera(self, case_number: str) -> dict[str, Any]:
        cn = self._normalize_case(case_number)
        fk_caso = self.datalake.resolve_fk_caso(cn)
        dim = None
        if fk_caso:
            dim = self.olap.get_record("dim_caso", str(fk_caso))

        asig_df = self.tx.read_table("app_asignaciones")
        asig = None
        if not asig_df.empty:
            mask = (
                asig_df["case_number"].astype(str).str.upper() == cn.upper()
            ) & (asig_df["estado_asignacion"].astype(str) == "Activa")
            if mask.any():
                asig = asig_df[mask].iloc[0].to_dict()

        bitacora = self._latest_bitacora(cn)
        if bitacora:
            avance = _safe_int(bitacora.get("avance_pct"))
            estado_caso = bitacora.get("estado_caso")
        elif asig:
            avance_raw = asig.get("avance_pct_actual")
            if pd.isna(avance_raw):
                estado_snap = str(
                    asig.get("estado_caso_snapshot") or (dim or {}).get("estado_caso") or ""
                )
                avance = _avance_por_estado(estado_snap)
            else:
                avance = _safe_int(avance_raw)
            estado_caso = (
                asig.get("estado_caso_snapshot") or (dim or {}).get("estado_caso")
            )
        else:
            avance = 0
            estado_caso = (dim or {}).get("estado_caso")

        if asig:
            asig = _json_safe(asig)
        if dim:
            dim = _json_safe(dim)

        return {
            "case_number": cn,
            "fk_caso": fk_caso,
            "dim_caso": dim,
            "asignacion": asig,
            "avance_pct": avance,
            "estado_caso": estado_caso,
            "expediente": self._find_expediente(cn),
        }

    def detalles_generales(self, case_number: str) -> dict[str, Any]:
        # Expedientes registrados manualmente describen sus propios datos del
        # hecho (no existen en el Data Lake crimes_220k).
        exp = self._find_expediente(case_number)
        if exp:
            return self._detalles_from_expediente(exp)
        return self.datalake.get_hechos_by_case_number(case_number)

    def _detective_activo_nombre(self, case_number: str) -> str | None:
        df = self.tx.read_table("app_asignaciones")
        if df.empty:
            return None
        cn = self._normalize_case(case_number).upper()
        mask = (
            (df["case_number"].astype(str).str.upper() == cn)
            & (df["estado_asignacion"].astype(str) == "Activa")
        )
        if not mask.any():
            return None
        nombre = df[mask].iloc[0].to_dict().get("detective_nombre")
        return str(nombre) if nombre else None

    def _detalles_from_expediente(self, exp: dict[str, Any]) -> dict[str, Any]:
        fecha = str(exp.get("fecha_hecho") or "")
        anio = fecha[:4] if len(fecha) >= 4 and fecha[:4].isdigit() else None
        cn = exp.get("case_number")

        def _v(key: str) -> Any:
            val = exp.get(key)
            s = str(val).strip() if val is not None else ""
            return s or None

        resumen = {
            "case_number": cn,
            "primary_type": _v("tipo_delito"),
            "description": _v("descripcion"),
            "date": fecha or None,
            "district": _v("distrito"),
            "beat": _v("sector"),
            "ward": _v("zona"),
            "block": _v("cuadra"),
            "location_description": _v("lugar_hecho") or _v("ubicacion"),
            "latitude": None,
            "longitude": None,
            "location": _v("ubicacion"),
            "arrest": _v("arresto"),
            "domestic": _v("violencia_domestica"),
            "year": anio,
            "iucr": _v("iucr"),
            "fbi_code": _v("fbi_code"),
            "estado_caso": _v("estado"),
            "prioridad_caso": _v("prioridad"),
            "investigador_asignado": self._detective_activo_nombre(cn),
            "total_registros_lake": 0,
        }
        return {
            "case_number": cn,
            "found": True,
            "hechos": [resumen],
            "resumen": resumen,
            "source": "expediente:registro-manual",
        }

    def list_involucrados(self, case_number: str) -> list[dict[str, Any]]:
        fk_caso = self.datalake.resolve_fk_caso(case_number)
        if not fk_caso:
            return []

        rel_df = self.tx.read_table("app_caso_involucrado")
        inv_df = self.tx.read_table("app_involucrados")
        if rel_df.empty or inv_df.empty:
            return []

        rels = rel_df[rel_df["fk_caso"].astype(int) == fk_caso]
        items = []
        for rel in rels.to_dict(orient="records"):
            inv = inv_df[inv_df["id_involucrado"].astype(int) == int(rel["fk_involucrado"])]
            if inv.empty:
                continue
            row = inv.iloc[0].to_dict()
            items.append(
                {
                    "id_relacion": int(rel["id_relacion"]),
                    "id_involucrado": int(row["id_involucrado"]),
                    "tipo_relacion": rel.get("tipo_relacion"),
                    "declaracion": rel.get("declaracion"),
                    "nombres": row.get("nombres"),
                    "apellidos": row.get("apellidos"),
                    "identificacion": row.get("identificacion"),
                    "fecha_nacimiento": row.get("fecha_nacimiento"),
                    "antecedentes": row.get("antecedentes"),
                }
            )
        return items

    def add_involucrado(
        self,
        case_number: str,
        *,
        user: dict[str, Any],
        data: dict[str, Any],
        foto: Any = None,
    ) -> dict[str, Any]:
        fk_caso = self.datalake.resolve_fk_caso(case_number)
        if not fk_caso:
            raise ValueError("Caso no encontrado en dim_caso")

        tipo = str(data.get("tipo_relacion", "Testigo"))
        if tipo not in TIPOS_INVOLUCRADO:
            raise ValueError(f"tipo_relacion debe ser uno de: {TIPOS_INVOLUCRADO}")

        from packages.involucrados.services.involucrados_service import (
            InvolucradosService,
        )

        inv_svc = InvolucradosService()
        identificacion = inv_svc.validar_identificacion(data.get("identificacion", ""))

        inv_row = {
            "identificacion": identificacion,
            "nombres": str(data.get("nombres", "")).strip(),
            "apellidos": str(data.get("apellidos", "")).strip(),
            "fecha_nacimiento": data.get("fecha_nacimiento", "") or "",
            "antecedentes": str(data.get("antecedentes", "")).strip(),
            "alias": str(data.get("alias", "")).strip(),
            "genero": str(data.get("genero", "")).strip(),
            "nacionalidad": str(data.get("nacionalidad", "")).strip(),
            "telefono": str(data.get("telefono", "")).strip(),
            "direccion": str(data.get("direccion", "")).strip(),
            "estado_civil": str(data.get("estado_civil", "")).strip(),
            "ocupacion": str(data.get("ocupacion", "")).strip(),
            "observaciones": str(data.get("observaciones", "")).strip(),
            "foto_url": "",
            "fecha_registro": utc_now_iso(),
            "fk_usuario_registro": int(user.get("id_usuario") or 0),
            "actualizado_en": utc_now_iso(),
        }
        created_inv = self.tx.append_row("app_involucrados", inv_row)
        if foto is not None:
            try:
                inv_svc.set_foto(
                    int(created_inv["id_involucrado"]),
                    file_obj=foto,
                    filename=getattr(foto, "name", "foto.jpg"),
                    user=user,
                )
            except Exception:
                pass
        rel_row = {
            "fk_caso": fk_caso,
            "fk_involucrado": int(created_inv["id_involucrado"]),
            "tipo_relacion": tipo,
            "declaracion": str(data.get("declaracion", "")).strip(),
            "fecha_asociacion": utc_now_iso(),
        }
        created_rel = self.tx.append_row("app_caso_involucrado", rel_row)
        return {**created_inv, **created_rel}

    def list_evidencias(self, case_number: str) -> list[dict[str, Any]]:
        # Delegado al paquete P06 (evidencias_digitales) — fuente única de verdad.
        from packages.evidencias_digitales.services.evidencias_service import EvidenciasService

        return EvidenciasService().list_by_case(case_number)

    def upload_evidencia(
        self,
        case_number: str,
        *,
        user: dict[str, Any],
        file_obj: Any,
        filename: str,
        tipo_evidencia: str = "Multimedia",
    ) -> dict[str, Any]:
        # Delegado al paquete P06: calcula hash SHA-256 e inicia la cadena de custodia.
        from packages.evidencias_digitales.services.evidencias_service import EvidenciasService

        return EvidenciasService().upload(
            case_number,
            user=user,
            file_obj=file_obj,
            filename=filename,
            tipo_evidencia=tipo_evidencia,
        )

    def list_bitacora(self, case_number: str) -> list[dict[str, Any]]:
        df = self.tx.read_table("app_expediente_bitacora")
        if df.empty:
            return []
        cn = self._normalize_case(case_number).upper()
        mask = df["case_number"].astype(str).str.upper() == cn
        items = df[mask].sort_values("fecha_hora", ascending=False)
        return [_json_safe(r) for r in items.to_dict(orient="records")]

    def _latest_bitacora(self, case_number: str) -> dict | None:
        items = self.list_bitacora(case_number)
        return items[0] if items else None

    def check_close_requirements(self, case_number: str, *, avance_pct: int | None = None) -> dict[str, Any]:
        """RN-09: valida los criterios de completitud y custodia para cerrar un expediente.

        Devuelve {"ok": bool, "faltantes": [str], "checks": {...}}.
        """
        cn = self._normalize_case(case_number)
        involucrados = self.list_involucrados(cn)
        evidencias = self.list_evidencias(cn)

        tiene_involucrados = len(involucrados) > 0
        tiene_evidencias = len(evidencias) > 0
        # Custodia: ninguna evidencia debe haber quedado fuera de custodia (p.ej. "Destruida").
        custodia_ok = all(
            str(ev.get("estado_custodia") or "").strip().lower() != "destruida"
            for ev in evidencias
        )
        avance_ok = True if avance_pct is None else int(avance_pct) >= 100

        faltantes: list[str] = []
        if not tiene_involucrados:
            faltantes.append("Debe registrar al menos un involucrado (víctima, sospechoso o testigo).")
        if not tiene_evidencias:
            faltantes.append("Debe cargar al menos una evidencia digital.")
        if not custodia_ok:
            faltantes.append("Hay evidencias con custodia rota (estado «Destruida»); revise la cadena de custodia.")
        if not avance_ok:
            faltantes.append("El avance del caso debe ser 100% para cerrarlo.")

        return {
            "ok": not faltantes,
            "faltantes": faltantes,
            "checks": {
                "involucrados": tiene_involucrados,
                "evidencias": tiene_evidencias,
                "custodia": custodia_ok,
                "avance": avance_ok,
            },
        }

    def add_bitacora_entry(
        self,
        case_number: str,
        *,
        user: dict[str, Any],
        nota: str,
        avance_pct: int,
        estado_caso: str,
    ) -> dict[str, Any]:
        cn = self._normalize_case(case_number)
        fk_caso = self.datalake.resolve_fk_caso(cn)
        if not fk_caso:
            raise ValueError("Caso no encontrado")

        avance_pct = max(0, min(100, int(avance_pct)))
        estado = str(estado_caso).strip()
        if estado not in ESTADOS_CASO:
            raise ValueError(f"estado_caso inválido. Use: {ESTADOS_CASO}")

        # RN-09 (CU-O25): solo se puede cerrar si cumple completitud y custodia.
        if estado in ESTADOS_CIERRE:
            req = self.check_close_requirements(cn, avance_pct=avance_pct)
            if not req["ok"]:
                raise ValueError(
                    "No se puede cerrar el expediente (RN-09). " + " ".join(req["faltantes"])
                )

        autor = f"{user.get('nombres', '')} {user.get('apellidos', '')}".strip()
        row = {
            "case_number": cn,
            "fk_caso": fk_caso,
            "fk_usuario": int(user["id_usuario"]),
            "autor_nombre": autor,
            "nota": nota.strip(),
            "avance_pct": avance_pct,
            "estado_caso": estado,
            "fecha_hora": utc_now_iso(),
        }
        created = self.tx.append_row("app_expediente_bitacora", row)

        try:
            self.olap.update_record("dim_caso", str(fk_caso), {"estado_caso": estado})
        except Exception:
            pass

        asig_df = self.tx.read_table("app_asignaciones")
        if not asig_df.empty:
            mask = (
                (asig_df["case_number"].astype(str).str.upper() == cn.upper())
                & (asig_df["estado_asignacion"].astype(str) == "Activa")
            )
            if mask.any():
                asig_df.loc[mask, "estado_caso_snapshot"] = estado
                if "avance_pct_actual" not in asig_df.columns:
                    asig_df["avance_pct_actual"] = 0
                asig_df.loc[mask, "avance_pct_actual"] = avance_pct
                self.tx.write_table("app_asignaciones", asig_df)

        try:
            from packages.dashboard_analitica.services.summary_materializer import (
                refresh_investigation_dashboard_metrics,
            )

            refresh_investigation_dashboard_metrics()
        except Exception:
            pass

        try:
            from core.cache.invalidation import bump_cache_generation

            bump_cache_generation()
        except Exception:
            pass

        return created

    # ------------------------------------------------------------------ #
    # Gestión de Expedientes Criminales (CU-O21..O24) — ciclo de vida.    #
    # ------------------------------------------------------------------ #
    def catalogos(self) -> dict[str, Any]:
        """Opciones para los formularios: distritos reales del sistema (los del dashboard)."""
        return {
            "distritos": self._distritos_sistema(),
            "tipos_delito": list(TIPOS_DELITO),
            "prioridades": list(PRIORIDADES_EXPEDIENTE),
        }

    def _distritos_sistema(self) -> list[str]:
        """Distritos del sistema, normalizados (misma lista que muestra el dashboard)."""
        raw: list[str] = []
        # 1) Fuente preferida: el mismo catálogo de filtros del dashboard.
        try:
            from packages.dashboard_analitica.services.dashboard_service import (
                DashboardService,
            )

            raw = list(DashboardService().filter_options().get("distritos") or [])
        except Exception:
            raw = []
        # 2) Respaldo: dim_distrito_policial directo.
        if not raw:
            try:
                an = self.datalake._analytics
                src = an._s3_uri(self.olap._object_key("dim_distrito_policial"))
                rows = an.connection().execute(
                    f"""
                    SELECT DISTINCT CAST(district AS VARCHAR) AS v
                    FROM read_parquet('{src}')
                    WHERE district IS NOT NULL
                      AND TRIM(CAST(district AS VARCHAR)) != ''
                    """
                ).fetchall()
                raw = [str(r[0]) for r in rows]
            except Exception:
                raw = []

        # Normaliza formatos mezclados ('003', '03', '3' → 3) y deduplica.
        nums: set[int] = set()
        otros: set[str] = set()
        for v in raw:
            s = str(v).strip()
            if not s:
                continue
            try:
                nums.add(int(s))
            except ValueError:
                otros.add(s)
        distritos = [f"{n:03d}" for n in sorted(nums)]
        distritos.extend(sorted(otros))
        return distritos

    def _expedientes_df(self) -> pd.DataFrame:
        return self.tx.read_table("app_expedientes")

    def _find_expediente(self, case_number: str) -> dict[str, Any] | None:
        df = self._expedientes_df()
        if df.empty:
            return None
        cn = self._normalize_case(case_number).upper()
        mask = df["case_number"].astype(str).str.upper() == cn
        if not mask.any():
            return None
        return _json_safe(df[mask].iloc[0].to_dict())

    def is_creator(self, fk_creador: int, case_number: str) -> bool:
        exp = self._find_expediente(case_number)
        if not exp:
            return False
        try:
            return int(exp.get("fk_creador") or 0) == int(fk_creador)
        except (TypeError, ValueError):
            return False

    def _case_number_exists(self, case_number: str) -> bool:
        cn = self._normalize_case(case_number).upper()
        if not cn:
            return False
        if self._find_expediente(cn):
            return True
        # También evita colisión con casos del Data Lake (dim_caso).
        try:
            return self.datalake.resolve_fk_caso(cn) is not None
        except Exception:
            return False

    def find_similar(self, *, case_number: str = "", titulo: str = "") -> list[dict[str, Any]]:
        """Sugerencias de duplicados por número exacto o título parecido."""
        df = self._expedientes_df()
        if df.empty:
            return []
        df = df[df["estado"].astype(str) != "ELIMINADO"]
        if df.empty:
            return []
        cn = self._normalize_case(case_number).upper()
        tit = str(titulo or "").strip().lower()
        mask = pd.Series(False, index=df.index)
        if cn:
            mask |= df["case_number"].astype(str).str.upper() == cn
        if len(tit) >= 4:
            mask |= df["titulo"].astype(str).str.lower().str.contains(tit, na=False, regex=False)
        hits = df[mask]
        return [
            {
                "case_number": r.get("case_number"),
                "titulo": r.get("titulo"),
                "estado": r.get("estado"),
                "tipo_delito": r.get("tipo_delito"),
            }
            for r in (_json_safe(x) for x in hits.head(8).to_dict(orient="records"))
        ]

    # ── Incidentes vinculados ──────────────────────────────────────────
    _INCIDENTE_COLS_LINK = ("fk_expediente", "expediente_case_number", "fecha_vinculacion")

    def _incidentes_df(self) -> pd.DataFrame:
        df = self.tx.read_table("app_incidentes")
        if not df.empty:
            for col in self._INCIDENTE_COLS_LINK:
                if col not in df.columns:
                    df[col] = ""
        return df

    @staticmethod
    def _incidente_public(row: dict[str, Any]) -> dict[str, Any]:
        link = str(row.get("expediente_case_number") or "").strip()
        return {
            "id_incidente": _safe_int(row.get("id_incidente")),
            "codigo": _json_safe(row.get("codigo")),
            "tipo": _json_safe(row.get("tipo")),
            "descripcion": _json_safe(row.get("descripcion")),
            "ubicacion": _json_safe(row.get("ubicacion")),
            "prioridad": _json_safe(row.get("prioridad")),
            "estado": _json_safe(row.get("estado")),
            "fecha_reporte": _json_safe(row.get("fecha_reporte")),
            "expediente_case_number": link or None,
        }

    def buscar_incidentes(
        self,
        *,
        q: str = "",
        solo_disponibles: bool = True,
        excluir_case: str = "",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Busca incidentes por código, fecha, lugar o tipo para vincularlos a un expediente."""
        df = self._incidentes_df()
        if df.empty:
            return []
        excl = self._normalize_case(excluir_case).upper()
        q_low = str(q or "").strip().lower()
        rows: list[dict[str, Any]] = []
        for r in df.sort_values("id_incidente", ascending=False).to_dict(orient="records"):
            link = str(r.get("expediente_case_number") or "").strip()
            if solo_disponibles and link and link.upper() != excl:
                continue
            if q_low:
                hay = " ".join(
                    str(r.get(k) or "")
                    for k in ("codigo", "ubicacion", "tipo", "descripcion", "fecha_reporte")
                ).lower()
                if q_low not in hay:
                    continue
            rows.append(self._incidente_public(r))
            if len(rows) >= max(1, int(limit)):
                break
        return rows

    def incidentes_de_expediente(self, case_number: str) -> list[dict[str, Any]]:
        df = self._incidentes_df()
        if df.empty:
            return []
        cn = self._normalize_case(case_number).upper()
        mask = df["expediente_case_number"].astype(str).str.upper() == cn
        if not mask.any():
            return []
        sub = df[mask].sort_values("id_incidente", ascending=False)
        return [self._incidente_public(r) for r in sub.to_dict(orient="records")]

    def _normalize_incidente_ids(self, raw: Any) -> list[int]:
        if raw is None:
            return []
        if not isinstance(raw, (list, tuple, set)):
            raw = [raw]
        out: list[int] = []
        for v in raw:
            try:
                out.append(int(v))
            except (TypeError, ValueError):
                continue
        # Únicos, preservando orden.
        seen: set[int] = set()
        return [x for x in out if not (x in seen or seen.add(x))]

    def reconciliar_incidentes(
        self,
        case_number: str,
        fk_caso: int,
        desired_ids: list[int],
        *,
        requerir_minimo: bool = True,
    ) -> dict[str, Any]:
        """Sincroniza los incidentes vinculados a un expediente con el conjunto deseado."""
        desired = set(self._normalize_incidente_ids(desired_ids))
        df = self._incidentes_df()
        if df.empty:
            if desired:
                raise ValueError("No hay incidentes registrados para vincular.")
            return {"vinculados": [], "agregados": [], "removidos": []}
        cn = self._normalize_case(case_number).upper()
        existing = {int(x) for x in df["id_incidente"].tolist()}
        for iid in desired:
            if iid not in existing:
                raise ValueError(f"El incidente #{iid} no existe.")
            sub = df[df["id_incidente"].astype("Int64") == iid]
            link = str(sub.iloc[0].get("expediente_case_number") or "").strip().upper()
            if link and link != cn:
                codigo = str(sub.iloc[0].get("codigo") or f"#{iid}")
                raise ValueError(
                    f"El incidente {codigo} ya pertenece al expediente {link}."
                )

        current_mask = df["expediente_case_number"].astype(str).str.upper() == cn
        current = {int(x) for x in df[current_mask]["id_incidente"].tolist()}
        # No se puede dejar sin incidentes a un expediente que ya tenía alguno.
        if requerir_minimo and not desired and current:
            raise ValueError(
                "El expediente debe conservar al menos un incidente vinculado."
            )
        to_add = desired - current
        to_remove = current - desired
        now = utc_now_iso()
        for iid in to_add:
            m = df["id_incidente"].astype("Int64") == iid
            df.loc[m, "fk_expediente"] = str(int(fk_caso)) if fk_caso else ""
            df.loc[m, "expediente_case_number"] = str(case_number)
            df.loc[m, "fecha_vinculacion"] = now
        for iid in to_remove:
            m = df["id_incidente"].astype("Int64") == iid
            df.loc[m, "fk_expediente"] = ""
            df.loc[m, "expediente_case_number"] = ""
            df.loc[m, "fecha_vinculacion"] = ""
        if to_add or to_remove:
            self.tx.write_table("app_incidentes", df)
        return {
            "vinculados": sorted(desired),
            "agregados": sorted(to_add),
            "removidos": sorted(to_remove),
        }

    def register_expediente(self, *, user: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        case_number = self._normalize_case(str(data.get("case_number", "")))
        titulo = str(data.get("titulo", "")).strip()
        tipo_delito = str(data.get("tipo_delito", "")).strip()
        descripcion = str(data.get("descripcion", "")).strip()
        ubicacion = str(data.get("ubicacion", "")).strip()
        prioridad = str(data.get("prioridad", "Media")).strip() or "Media"
        fecha_hecho = str(data.get("fecha_hecho") or data.get("fecha") or "").strip()

        # RN: un expediente siempre se origina a partir de al menos un incidente.
        incidente_ids = self._normalize_incidente_ids(data.get("incidente_ids"))
        if not incidente_ids:
            raise ValueError(
                "Vincule al menos un incidente: el expediente se origina a partir "
                "del incidente que desencadena la investigación."
            )

        if not case_number:
            raise ValueError("El número de caso es obligatorio.")
        if not titulo:
            raise ValueError("El título del expediente es obligatorio.")
        if not tipo_delito:
            raise ValueError("El tipo de delito es obligatorio.")
        if prioridad not in PRIORIDADES_EXPEDIENTE:
            raise ValueError(f"Prioridad inválida. Use: {', '.join(PRIORIDADES_EXPEDIENTE)}.")
        if fecha_hecho:
            # Valida formato y que no sea una fecha futura (RN: el hecho ya ocurrió).
            fecha_hecho = _parse_fecha_hecho(fecha_hecho).isoformat()
        if self._case_number_exists(case_number):
            raise ValueError(
                f"Ya existe un expediente o caso con el número «{case_number}». "
                "Verifique antes de registrar uno nuevo."
            )

        # Valida disponibilidad de los incidentes ANTES de crear nada (evita huérfanos).
        inc_df = self._incidentes_df()
        existing_inc = {int(x) for x in inc_df["id_incidente"].tolist()} if not inc_df.empty else set()
        for iid in incidente_ids:
            if iid not in existing_inc:
                raise ValueError(f"El incidente #{iid} no existe.")
            sub = inc_df[inc_df["id_incidente"].astype("Int64") == iid]
            link = str(sub.iloc[0].get("expediente_case_number") or "").strip()
            if link:
                codigo = str(sub.iloc[0].get("codigo") or f"#{iid}")
                raise ValueError(
                    f"El incidente {codigo} ya pertenece al expediente {link}."
                )

        # Ancla analítica: crea el registro dim_caso para que las pestañas
        # (involucrados, evidencias, bitácora, PDF) operen sobre un fk_caso real.
        dim_row = {
            "case_number": case_number,
            "estado_caso": "Abierto",
            "prioridad_caso": prioridad,
            "fecha_reporte": fecha_hecho or utc_now_iso()[:10],
            "observaciones": descripcion or titulo,
            "investigador_asignado": "",
        }
        created_dim = self.olap.create_record("dim_caso", dim_row)
        fk_caso = int(created_dim.get("id"))

        autor = f"{user.get('nombres', '')} {user.get('apellidos', '')}".strip()
        now = utc_now_iso()
        exp_row = {
            "case_number": case_number,
            "fk_caso": fk_caso,
            "titulo": titulo,
            "descripcion": descripcion,
            "tipo_delito": tipo_delito,
            "ubicacion": ubicacion,
            "prioridad": prioridad,
            "fecha_hecho": fecha_hecho,
            "estado": "ACTIVO",
            "distrito": str(data.get("distrito", "")).strip(),
            "sector": str(data.get("sector", "")).strip(),
            "zona": str(data.get("zona", "")).strip(),
            "cuadra": str(data.get("cuadra", "")).strip(),
            "lugar_hecho": str(data.get("lugar_hecho", "")).strip(),
            "iucr": str(data.get("iucr", "")).strip(),
            "fbi_code": str(data.get("fbi_code", "")).strip(),
            "arresto": str(data.get("arresto", "")).strip(),
            "violencia_domestica": str(data.get("violencia_domestica", "")).strip(),
            "fk_creador": int(user.get("id_usuario") or 0),
            "creador_nombre": autor or str(user.get("email") or "Oficial"),
            "creado_en": now,
            "actualizado_en": now,
            "motivo_estado": "Expediente registrado",
            "fk_autoriza": 0,
            "autoriza_nombre": "",
        }
        created = self.tx.append_row("app_expedientes", exp_row)

        # Vincula los incidentes de origen al expediente recién creado.
        vinculo = self.reconciliar_incidentes(case_number, fk_caso, incidente_ids)

        self._bump_caches()
        result = _json_safe(created)
        result["incidentes_vinculados"] = vinculo.get("vinculados", [])
        return result

    def search_expedientes(
        self,
        *,
        q: str = "",
        estado: str = "",
        page: int = 1,
        per_page: int = 10,
    ) -> dict[str, Any]:
        """Listado unificado: expedientes (registro manual) + casos ya existentes.

        Cada expediente registrado por el Oficial también vive en dim_caso, por lo
        que la lista se construye sobre el universo de casos (paginado vía DuckDB)
        y se superponen los datos del expediente cuando existen.
        """
        from packages.asignacion_investigaciones.services.casos_operativos_store import (
            CasosOperativosStore,
        )

        page = max(1, int(page or 1))
        per_page = max(1, min(int(per_page or 10), 100))

        # Mapa de expedientes por número de caso (incluye datos de negocio + lifecycle).
        exp_df = self._expedientes_df()
        exp_by_cn: dict[str, dict[str, Any]] = {}
        eliminados: set[str] = set()
        if not exp_df.empty:
            for raw in exp_df.to_dict(orient="records"):
                row = _json_safe(raw)
                cn = str(row.get("case_number") or "").strip().upper()
                if not cn:
                    continue
                if str(row.get("estado") or "").upper() == "ELIMINADO":
                    eliminados.add(cn)
                    continue
                exp_by_cn[cn] = row

        store = CasosOperativosStore()
        res = store.search_casos(q=q, estado=estado, page=page, per_page=per_page)

        items: list[dict[str, Any]] = []
        for it in res.get("items", []):
            cn = str(it.get("case_number") or "").strip()
            cn_u = cn.upper()
            if cn_u in eliminados:
                continue
            exp = exp_by_cn.get(cn_u)
            fecha = (
                (exp.get("fecha_hecho") if exp and exp.get("fecha_hecho") else None)
                or it.get("fecha_hecho")
                or it.get("fecha_reporte")
            )
            base = {
                "case_number": cn,
                "tipo_delito": (
                    (exp.get("tipo_delito") if exp and exp.get("tipo_delito") else None)
                    or it.get("primary_type")
                ),
                "distrito": it.get("district"),
                "fecha": fecha,
                "estado": (exp.get("estado") if exp else it.get("estado_caso")),
                "prioridad": (exp.get("prioridad") if exp else it.get("prioridad_caso")),
                "detective": it.get("detective_actual") or it.get("investigador_asignado"),
                "es_expediente": exp is not None,
                "origen": "Expediente" if exp else "Caso",
            }
            items.append({**(exp or {}), **base})

        total = res.get("totalItems", len(items))
        return {
            "items": items,
            "page": res.get("page", page),
            "perPage": res.get("perPage", per_page),
            "totalItems": total,
            "totalPages": res.get("totalPages", 1),
            "message": res.get("message", ""),
        }

    def _fk_casos_por_involucrado(self, q_low: str) -> set[int]:
        if len(q_low) < 2:
            return set()
        inv = self.tx.read_table("app_involucrados")
        rel = self.tx.read_table("app_caso_involucrado")
        if inv.empty or rel.empty:
            return set()
        name = (
            inv["nombres"].astype(str) + " " + inv["apellidos"].astype(str)
        ).str.lower()
        ident = inv.get("identificacion")
        mask = name.str.contains(q_low, na=False, regex=False)
        if ident is not None:
            mask |= ident.astype(str).str.lower().str.contains(q_low, na=False, regex=False)
        inv_ids = set(int(x) for x in inv[mask]["id_involucrado"].tolist())
        if not inv_ids:
            return set()
        rel_hit = rel[rel["fk_involucrado"].astype("Int64").isin(list(inv_ids))]
        return set(int(x) for x in rel_hit["fk_caso"].tolist())

    def update_expediente(
        self, case_number: str, *, user: dict[str, Any], data: dict[str, Any]
    ) -> dict[str, Any]:
        exp = self._find_expediente(case_number)
        if not exp:
            raise ValueError("Expediente no encontrado.")
        estado = str(exp.get("estado") or "").upper()
        if estado == "ELIMINADO":
            raise ValueError("No se puede editar un expediente eliminado.")
        if estado == "ARCHIVADO":
            raise ValueError("El expediente está archivado y es de solo lectura.")
        if estado not in ESTADOS_EDITABLES:
            raise ValueError(f"El expediente no es editable en estado «{estado}».")

        campos = (
            "titulo",
            "descripcion",
            "tipo_delito",
            "ubicacion",
            "prioridad",
            "fecha_hecho",
            "distrito",
            "sector",
            "zona",
            "cuadra",
            "lugar_hecho",
            "iucr",
            "fbi_code",
            "arresto",
            "violencia_domestica",
        )
        antes: dict[str, Any] = {}
        despues: dict[str, Any] = {}
        for c in campos:
            if c not in data:
                continue
            nuevo = str(data.get(c) or "").strip()
            if c == "prioridad" and nuevo and nuevo not in PRIORIDADES_EXPEDIENTE:
                raise ValueError(f"Prioridad inválida. Use: {', '.join(PRIORIDADES_EXPEDIENTE)}.")
            if c == "fecha_hecho" and nuevo:
                # No se permite registrar un hecho con fecha futura.
                nuevo = _parse_fecha_hecho(nuevo).isoformat()
            actual = str(exp.get(c) or "")
            if nuevo != actual:
                antes[c] = actual
                despues[c] = nuevo

        # Reconcilia incidentes vinculados si el cliente envía el conjunto deseado.
        vinculo = None
        if "incidente_ids" in data:
            fk_caso = _safe_int(exp.get("fk_caso"))
            vinculo = self.reconciliar_incidentes(
                exp.get("case_number"),
                fk_caso,
                data.get("incidente_ids"),
            )
            if vinculo.get("agregados") or vinculo.get("removidos"):
                antes["incidentes"] = "actualizados"
                despues["incidentes"] = (
                    f"+{len(vinculo['agregados'])} / -{len(vinculo['removidos'])}"
                )

        if not despues:
            raise ValueError("No se detectaron cambios para guardar.")

        campos_persist = {k: v for k, v in despues.items() if k in campos}
        campos_persist["actualizado_en"] = utc_now_iso()
        self._update_expediente_row(case_number, campos_persist)

        # Mantiene coherencia con el ancla analítica dim_caso.
        try:
            fk_caso = int(exp.get("fk_caso") or 0)
            if fk_caso:
                dim_patch = {}
                if "prioridad" in despues:
                    dim_patch["prioridad_caso"] = despues["prioridad"]
                if "descripcion" in despues:
                    dim_patch["observaciones"] = despues["descripcion"]
                if "fecha_hecho" in despues:
                    dim_patch["fecha_reporte"] = despues["fecha_hecho"]
                if dim_patch:
                    self.olap.update_record("dim_caso", str(fk_caso), dim_patch)
        except Exception:
            pass

        self._bump_caches()
        return {"antes": antes, "despues": despues, "case_number": exp.get("case_number")}

    def change_estado(
        self,
        case_number: str,
        *,
        user: dict[str, Any],
        accion: str,
        motivo: str = "",
    ) -> dict[str, Any]:
        accion_map = {
            "cerrar": "CERRADO",
            "reabrir": "REABIERTO",
            "archivar": "ARCHIVADO",
            "eliminar": "ELIMINADO",
        }
        target = accion_map.get(str(accion or "").lower().strip())
        if not target:
            raise ValueError("Acción de estado no válida.")

        exp = self._find_expediente(case_number)
        if not exp:
            raise ValueError("Expediente no encontrado.")
        actual = str(exp.get("estado") or "ACTIVO").upper()
        if actual == "ELIMINADO":
            raise ValueError("El expediente ya fue eliminado lógicamente.")

        permitidos = TRANSICIONES_EXPEDIENTE.get(actual, set())
        if target not in permitidos:
            raise ValueError(
                f"Transición no permitida: «{actual}» → «{target}». "
                f"Transiciones válidas desde «{actual}»: "
                f"{', '.join(sorted(permitidos)) or 'ninguna'}."
            )

        motivo = str(motivo or "").strip()
        if not motivo:
            raise ValueError("El motivo es obligatorio para cambiar el estado del expediente.")

        autor = f"{user.get('nombres', '')} {user.get('apellidos', '')}".strip()
        patch: dict[str, Any] = {
            "estado": target,
            "motivo_estado": motivo,
            "actualizado_en": utc_now_iso(),
        }
        if target == "ELIMINADO":
            patch["fk_autoriza"] = int(user.get("id_usuario") or 0)
            patch["autoriza_nombre"] = autor or str(user.get("email") or "")

        self._update_expediente_row(case_number, patch)

        # Refleja archivado/cerrado en el ancla analítica (estado investigativo).
        try:
            fk_caso = int(exp.get("fk_caso") or 0)
            if fk_caso and target in ("CERRADO", "ARCHIVADO"):
                self.olap.update_record(
                    "dim_caso",
                    str(fk_caso),
                    {"estado_caso": "Cerrado" if target == "CERRADO" else "Archivado"},
                )
        except Exception:
            pass

        # Al cerrar/archivar, deja constancia en el historial de los incidentes
        # vinculados (quedan como parte del expediente).
        if target in ("CERRADO", "ARCHIVADO"):
            try:
                incs = self.incidentes_de_expediente(case_number)
                if incs:
                    codigos = ", ".join(str(i.get("codigo")) for i in incs)
                    verbo = "cerrado" if target == "CERRADO" else "archivado"
                    # Escritura directa en la bitácora (constancia de historial),
                    # sin pasar por el gate de cierre RN-09.
                    self.tx.append_row(
                        "app_expediente_bitacora",
                        {
                            "case_number": case_number,
                            "fk_caso": _safe_int(exp.get("fk_caso")),
                            "fk_usuario": int(user.get("id_usuario") or 0),
                            "autor_nombre": autor or "Sistema",
                            "nota": (
                                f"Expediente {verbo}. Incidentes vinculados que pasan al "
                                f"historial del expediente: {codigos}. Motivo: {motivo}"
                            ),
                            "avance_pct": 100 if target == "ARCHIVADO" else 90,
                            "estado_caso": "Archivado" if target == "ARCHIVADO" else "Cerrado",
                            "fecha_hora": utc_now_iso(),
                        },
                    )
            except Exception:
                pass

        self._bump_caches()
        return {
            "case_number": exp.get("case_number"),
            "estado_anterior": actual,
            "estado_nuevo": target,
            "motivo": motivo,
        }

    def _update_expediente_row(self, case_number: str, patch: dict[str, Any]) -> None:
        df = self._expedientes_df()
        if df.empty:
            raise ValueError("Expediente no encontrado.")
        cn = self._normalize_case(case_number).upper()
        idx = df.index[df["case_number"].astype(str).str.upper() == cn]
        if idx.empty:
            raise ValueError("Expediente no encontrado.")
        for col, val in patch.items():
            if col not in df.columns:
                df[col] = ""
            df.at[idx[0], col] = val
        self.tx.write_table("app_expedientes", df)

    def _bump_caches(self) -> None:
        try:
            from core.cache.invalidation import bump_cache_generation

            bump_cache_generation()
        except Exception:
            pass
