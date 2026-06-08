"""
Tabla materializada app_dashboard_summary — lectura O(1) para el dashboard (OLAP precalculado).
"""

from __future__ import annotations

import json
import time
from typing import Any

from packages.shared.minio_transactional import SCHEMAS, TransactionalMinioStore, utc_now_iso

SUMMARY_KEYS = (
    "overview",
    "filter_options",
    "heat_map",
    "detective_ranking",
    "operational",
    "agg_rollups",
)


class DashboardSummaryStore:
    """Persiste y lee métricas precalculadas desde MinIO transaccional."""

    def __init__(self) -> None:
        self.tx = TransactionalMinioStore()

    def ensure_table(self) -> None:
        try:
            self.tx.read_table("app_dashboard_summary")
        except Exception:
            import pandas as pd

            self.tx.write_table(
                "app_dashboard_summary",
                pd.DataFrame(columns=SCHEMAS["app_dashboard_summary"]),
            )

    def is_ready(self) -> bool:
        self.ensure_table()
        df = self.tx.read_table("app_dashboard_summary")
        if df.empty:
            return False
        return bool((df["clave"] == "overview").any())

    def get_payload(self, clave: str) -> dict[str, Any] | list[Any] | None:
        self.ensure_table()
        df = self.tx.read_table("app_dashboard_summary")
        if df.empty:
            return None
        rows = df[df["clave"].astype(str) == clave]
        if rows.empty:
            return None
        raw = rows.iloc[0].get("payload_json", "")
        if not raw:
            return None
        try:
            return json.loads(str(raw))
        except json.JSONDecodeError:
            return None

    def get_meta(self) -> dict[str, Any]:
        self.ensure_table()
        df = self.tx.read_table("app_dashboard_summary")
        if df.empty:
            return {"ready": False, "updated_at": None, "filas_hechos": 0}
        overview = df[df["clave"] == "overview"]
        if overview.empty:
            return {"ready": False, "updated_at": None, "filas_hechos": 0}
        row = overview.iloc[0]
        return {
            "ready": True,
            "updated_at": row.get("actualizado_en"),
            "filas_hechos": int(row.get("filas_hechos") or 0),
            "duracion_ms": float(row.get("duracion_ms") or 0),
        }

    def upsert_payload(self, clave: str, payload: Any) -> None:
        import pandas as pd

        self.ensure_table()
        df = self.tx.read_table("app_dashboard_summary")
        now = utc_now_iso()
        payload_json = json.dumps(payload, ensure_ascii=False, default=str)
        mask = df["clave"].astype(str) == clave
        if mask.any():
            df.loc[mask, "payload_json"] = payload_json
            df.loc[mask, "actualizado_en"] = now
        else:
            next_id = int(df["id_summary"].max()) + 1 if not df.empty else 1
            filas = int(df["filas_hechos"].max()) if not df.empty and "filas_hechos" in df.columns else 0
            duracion = float(df["duracion_ms"].max()) if not df.empty and "duracion_ms" in df.columns else 0.0
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        [
                            {
                                "id_summary": next_id,
                                "clave": clave,
                                "payload_json": payload_json,
                                "actualizado_en": now,
                                "filas_hechos": filas,
                                "duracion_ms": duracion,
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )
        self.tx.write_table("app_dashboard_summary", df)

    def replace_all(self, entries: dict[str, Any], *, filas_hechos: int, duracion_ms: float) -> None:
        import pandas as pd

        self.ensure_table()
        now = utc_now_iso()
        rows = []
        for idx, (clave, payload) in enumerate(entries.items(), start=1):
            rows.append(
                {
                    "id_summary": idx,
                    "clave": clave,
                    "payload_json": json.dumps(payload, ensure_ascii=False, default=str),
                    "actualizado_en": now,
                    "filas_hechos": filas_hechos,
                    "duracion_ms": round(duracion_ms, 2),
                }
            )
        self.tx.write_table("app_dashboard_summary", pd.DataFrame(rows))

    def read_timing_ms(self) -> float:
        t0 = time.perf_counter()
        self.get_payload("overview")
        return round((time.perf_counter() - t0) * 1000, 3)
