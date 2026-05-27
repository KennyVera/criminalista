"""
Claves compuestas y mapeo FK vectorizado (O(n) sin pd.merge sobre el hecho completo).
"""

from __future__ import annotations

import pandas as pd

_KEY_SEP = "\x1f"


def as_merge_str(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().replace({"nan": "", "None": "", "<NA>": ""})


def composite_key(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    """Clave unica estable para indexar / mapear FKs."""
    parts = [as_merge_str(df[c]) for c in cols if c in df.columns]
    if not parts:
        return pd.Series([""] * len(df), index=df.index)
    key = parts[0]
    for part in parts[1:]:
        key = key + _KEY_SEP + part
    return key


def map_foreign_key(
    raw_df: pd.DataFrame,
    dim: pd.DataFrame,
    raw_cols: list[str],
    dim_cols: list[str],
) -> pd.Series:
    """Mapea filas crudas al id de dimension sin merge (hash join via Series.map)."""
    left_key = composite_key(raw_df, raw_cols)
    dim_work = dim[dim_cols + ["id"]].copy()
    right_key = composite_key(dim_work, dim_cols)
    id_map = pd.Series(
        pd.to_numeric(dim_work["id"], errors="coerce").values,
        index=right_key.values,
    )
    # Si hay claves duplicadas en dim, quedarse con la primera
    id_map = id_map[~id_map.index.duplicated(keep="first")]
    return left_key.map(id_map).astype("Int64")
