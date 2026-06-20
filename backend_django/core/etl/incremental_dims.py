"""
Construcción incremental de dimensiones — una pasada por chunks sin raw_df monolítico.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from core.etl.fast_keys import as_merge_str, composite_key
from core.services.minio_store import DIM_COLLECTIONS


@dataclass
class _IncrementalDim:
    name: str
    cols: list[str]
    key_cols: list[str]
    defaults: dict[str, Any] = field(default_factory=dict)
    key_to_id: dict[str, int] = field(default_factory=dict)
    rows: list[dict[str, Any]] = field(default_factory=list)

    def ingest(self, raw_df: pd.DataFrame) -> int:
        cols_present = [c for c in self.cols if c in raw_df.columns]
        if not cols_present:
            return 0
        subset = raw_df[cols_present].copy()
        for col in subset.columns:
            subset[col] = as_merge_str(subset[col])
        subset = subset.drop_duplicates(subset=self.key_cols, keep="first")
        keys = composite_key(subset, self.key_cols)
        added = 0
        for idx, key in keys.items():
            if key in self.key_to_id:
                continue
            new_id = len(self.key_to_id) + 1
            self.key_to_id[key] = new_id
            row = subset.loc[idx].to_dict()
            payload = {**row, "id": new_id, **self.defaults}
            self.rows.append(payload)
            added += 1
        return added

    def to_dataframe(self) -> pd.DataFrame:
        if not self.rows:
            return pd.DataFrame(columns=["id", *self.cols])
        df = pd.DataFrame(self.rows)
        if "id" not in df.columns:
            df.insert(0, "id", range(1, len(df) + 1))
        return df


class IncrementalDimStore:
    """Acumula dimensiones únicas chunk a chunk (memoria ~únicos, no ~hechos)."""

    def __init__(self) -> None:
        self._dims: dict[str, _IncrementalDim] = {}
        self._init_specs()

    def _init_specs(self) -> None:
        self._dims["dim_caso"] = _IncrementalDim(
            "dim_caso",
            ["case_number"],
            ["case_number"],
            defaults={"estado_caso": "Importado", "prioridad_caso": "Media"},
        )
        self._dims["dim_tipo_crimen"] = _IncrementalDim(
            "dim_tipo_crimen",
            ["iucr", "primary_type", "description", "fbi_code"],
            ["iucr", "primary_type"],
        )
        self._dims["dim_distrito_policial"] = _IncrementalDim(
            "dim_distrito_policial",
            ["beat", "district"],
            ["beat", "district"],
        )
        self._dims["dim_area_administrativa"] = _IncrementalDim(
            "dim_area_administrativa",
            ["ward", "community_area"],
            ["ward", "community_area"],
        )
        self._dims["dim_tiempo"] = _IncrementalDim(
            "dim_tiempo",
            ["date", "year"],
            ["date"],
        )
        self._dims["dim_ubicacion_lugar"] = _IncrementalDim(
            "dim_ubicacion_lugar",
            ["location_description", "block"],
            ["location_description", "block"],
        )
        self._dims["dim_arresto"] = _IncrementalDim(
            "dim_arresto",
            ["arrest"],
            ["arrest"],
        )
        self._dims["dim_violencia_domestica"] = _IncrementalDim(
            "dim_violencia_domestica",
            ["domestic"],
            ["domestic"],
        )
        self._dims["dim_actualizacion"] = _IncrementalDim(
            "dim_actualizacion",
            ["updated_on"],
            ["updated_on"],
        )
        self._geo_cols = ["latitude", "longitude", "location"]

    def _geo_dim(self) -> _IncrementalDim:
        if "dim_ubicacion_geografica" not in self._dims:
            self._dims["dim_ubicacion_geografica"] = _IncrementalDim(
                "dim_ubicacion_geografica",
                list(self._geo_cols),
                ["latitude", "longitude"],
            )
        return self._dims["dim_ubicacion_geografica"]

    def ingest_chunk(self, raw_df: pd.DataFrame) -> dict[str, int]:
        stats: dict[str, int] = {}
        for name in (
            "dim_caso",
            "dim_tipo_crimen",
            "dim_distrito_policial",
            "dim_area_administrativa",
            "dim_tiempo",
            "dim_ubicacion_lugar",
            "dim_arresto",
            "dim_violencia_domestica",
            "dim_actualizacion",
        ):
            stats[name] = self._dims[name].ingest(raw_df)

        geo_cols = list(self._geo_cols)
        for col in ("x_coordinate", "y_coordinate"):
            if col in raw_df.columns:
                geo_cols.append(col)
        geo = self._geo_dim()
        geo.cols = geo_cols
        stats["dim_ubicacion_geografica"] = geo.ingest(raw_df)
        return stats

    def to_dataframes(self) -> dict[str, pd.DataFrame]:
        out: dict[str, pd.DataFrame] = {}
        for name in DIM_COLLECTIONS:
            if name in self._dims:
                out[name] = self._dims[name].to_dataframe()
        return out

    @property
    def total_rows(self) -> int:
        return sum(len(d.rows) for d in self._dims.values())
