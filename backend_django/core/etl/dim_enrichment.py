"""
Enriquece dimensiones del ETL con todas las columnas del modelo (postgres_config).
Valores derivados del raw cuando es posible; el resto determinista por clave natural.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

TURNOS = ("Mañana", "Tarde", "Noche", "Madrugada")
TEMPORADAS = ("Invierno", "Primavera", "Verano", "Otoño")
NIVELES_RIESGO = ("Bajo", "Medio", "Alto")
TIPOS_ZONA = ("Urbana", "Residencial", "Comercial", "Industrial")


def _seed(*parts: str) -> int:
    h = hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()
    return int(h[:8], 16)


def _pick(options: tuple, *key: str) -> str:
    return options[_seed(*key) % len(options)]


def _hash_series(keys: pd.Series) -> pd.Series:
    """Hash estable y rapido (sin apply fila a fila)."""
    return pd.util.hash_pandas_object(keys.astype(str), index=False)


def _pick_series(options: tuple, keys: pd.Series) -> pd.Series:
    seeds = _hash_series(keys)
    idx = (seeds % len(options)).astype(np.int64)
    return pd.Series(np.take(np.array(options, dtype=object), idx), index=keys.index)


def _parse_datetime(series: pd.Series) -> pd.Series:
    """Parsea fechas estilo Chicago crimes (%m/%d/%Y ...)."""
    return pd.to_datetime(series, format="mixed", errors="coerce")


def _add_legacy_id(df: pd.DataFrame) -> pd.DataFrame:
    if "id" in df.columns:
        df["legacy_id"] = df["id"].astype(int)
    return df


def enrich_dim_tiempo(df: pd.DataFrame) -> pd.DataFrame:
    df = _add_legacy_id(df.copy())
    parsed = _parse_datetime(df["date"])
    df["year"] = parsed.dt.year.fillna(df.get("year")).astype("Int64").astype(str)
    df["month"] = parsed.dt.month
    df["day"] = parsed.dt.day
    df["hour"] = parsed.dt.hour
    df["day_of_week"] = parsed.dt.day_name()
    df["quarter"] = parsed.dt.quarter
    df["es_fin_de_semana"] = parsed.dt.weekday >= 5
    df["es_feriado"] = False
    df["temporada"] = parsed.dt.month.map(
        {
            12: "Invierno",
            1: "Invierno",
            2: "Invierno",
            3: "Primavera",
            4: "Primavera",
            5: "Primavera",
            6: "Verano",
            7: "Verano",
            8: "Verano",
            9: "Otoño",
            10: "Otoño",
            11: "Otoño",
        }
    )
    hours = parsed.dt.hour.fillna(12)
    df["turno"] = hours.apply(
        lambda h: "Madrugada"
        if h < 6
        else "Mañana"
        if h < 12
        else "Tarde"
        if h < 18
        else "Noche"
    )
    return df


def enrich_dim_distrito_policial(df: pd.DataFrame) -> pd.DataFrame:
    df = _add_legacy_id(df.copy())
    d = df["district"].astype(str).str.strip().replace("", "0")
    b = df["beat"].astype(str).str.strip()
    keys = d + "|" + b
    seeds = _hash_series(keys)
    df["nombre_distrito"] = "Distrito " + d + " - CPD Zone"
    df["jefe_distrito"] = "Cmdr. " + _pick_series(
        ("García", "Smith", "Johnson", "Williams", "Brown"), d
    )
    df["numero_oficiales"] = 80 + (seeds % 270)
    df["telefono_emergencias"] = "(312) 555-" + (1000 + (seeds % 8999)).astype(int).astype(str)
    df["direccion_sede"] = (100 + (seeds % 900)).astype(int).astype(str) + " W District " + d + " St, Chicago, IL"
    df["horario_atencion"] = "24/7"
    return df


def enrich_dim_arresto(df: pd.DataFrame) -> pd.DataFrame:
    df = _add_legacy_id(df.copy())
    val = df["arrest"].astype(str).str.lower()
    arrested = val.isin(("true", "1", "yes", "sí", "si", "y"))
    seeds = _hash_series("arrest|" + val)
    df["descripcion_arresto"] = np.where(
        arrested, "Detención en escena", "Sin detención reportada"
    )
    df["fecha_arresto"] = np.where(arrested, "Registrado en incidente", "")
    df["lugar_detencion"] = np.where(arrested, "Escena del hecho", "N/A")
    df["oficial_a_cargo"] = np.where(
        arrested, "Oficial #" + (100 + (seeds % 900)).astype(int).astype(str), ""
    )
    df["tipo_cargo"] = np.where(
        arrested,
        _pick_series(("Misdemeanor", "Felony", "Citation", "N/A"), val),
        "N/A",
    )
    df["fianza_requerida"] = arrested & (seeds % 2 == 0)
    df["monto_fianza"] = np.where(arrested, np.round((seeds % 50) * 500, 2), 0)
    return df


def _case_report_year(case_number: str) -> int:
    return 2000 + (_seed("yr", case_number) % 26)


def _case_estado(case_number: str) -> str:
    yr = _case_report_year(case_number)
    if yr < 2015:
        return _pick(("Cerrado", "Archivado", "Archivado"), case_number)
    if yr < 2020:
        return _pick(("Cerrado", "En investigación", "Archivado"), case_number)
    return _pick(("Abierto", "En investigación", "Cerrado", "Archivado"), case_number)


def enrich_dim_caso(df: pd.DataFrame) -> pd.DataFrame:
    df = _add_legacy_id(df.copy())
    cn = df["case_number"].astype(str)
    df["fecha_reporte"] = cn.map(
        lambda s: (
            f"{_case_report_year(s)}-{(_seed('caso', s) % 12) + 1:02d}-"
            f"{(_seed('caso2', s) % 28) + 1:02d}"
        )
    )
    df["investigador_asignado"] = cn.map(
        lambda s: f"Det. {_pick(('Martínez', 'Lee', 'Davis', 'Wilson'), s)}"
    )
    df["prioridad_caso"] = cn.map(lambda s: _pick(("Baja", "Media", "Alta", "Crítica"), s))
    df["estado_caso"] = cn.map(_case_estado)
    df["observaciones"] = cn.map(lambda s: f"Caso {s} - registro ETL CrimeTrack")
    return df


def enrich_dim_tipo_crimen(df: pd.DataFrame) -> pd.DataFrame:
    df = _add_legacy_id(df.copy())
    pt = df["primary_type"].astype(str)
    pt_upper = pt.str.upper()
    keys = pt + "|" + df["iucr"].astype(str)
    seeds = _hash_series(keys)
    grave = pt_upper.str.contains("ASSAULT|BATTERY|HOMICIDE|ROBBERY", regex=True)
    df["nivel_gravedad"] = np.where(grave, "Grave", _pick_series(("Leve", "Moderado"), pt))
    df["categoria_penal"] = pt.replace("", "General")
    df["requiere_arma"] = pt_upper.str.contains("ROBBERY|HOMICIDE") | (seeds % 5 == 0)
    df["es_reincidente"] = seeds % 7 == 0
    return df


def enrich_dim_area_administrativa(df: pd.DataFrame) -> pd.DataFrame:
    df = _add_legacy_id(df.copy())
    w = df["ward"].astype(str)
    ca = df["community_area"].astype(str)
    seeds = _hash_series(w + "|" + ca)
    df["nombre_comunidad"] = "Community Area " + ca + " — Ward " + w
    df["poblacion_estimada"] = 8000 + (seeds % 112000)
    df["alcalde_representante"] = "Ald. " + _pick_series(
        ("Taylor", "Moore", "Anderson", "Thomas"), w
    )
    df["nivel_socioeconomico"] = _pick_series(("Bajo", "Medio", "Alto", "Mixto"), w + ca)
    df["superficie_km2"] = np.round(1.5 + (seeds % 430) / 10.0, 2)
    return df


def enrich_dim_ubicacion_lugar(df: pd.DataFrame) -> pd.DataFrame:
    df = _add_legacy_id(df.copy())
    loc = df["location_description"].astype(str)
    loc_upper = loc.str.upper()
    keys = loc + "|" + df["block"].astype(str)
    seeds = _hash_series(keys)
    comercial = loc_upper.str.contains("STORE|LOT")
    df["tipo_zona"] = np.where(comercial, "Comercial", _pick_series(TIPOS_ZONA, loc))
    df["nivel_riesgo"] = _pick_series(NIVELES_RIESGO, loc)
    df["iluminacion"] = _pick_series(("Buena", "Regular", "Mala"), loc)
    df["vigilancia_camaras"] = seeds % 3 != 0
    return df


def enrich_dim_ubicacion_geografica(df: pd.DataFrame) -> pd.DataFrame:
    df = _add_legacy_id(df.copy())
    for col in ("x_coordinate", "y_coordinate"):
        if col not in df.columns:
            df[col] = ""
    lat = df["latitude"].astype(str)
    keys = lat + "|" + df["longitude"].astype(str)
    seeds = _hash_series(keys)
    df["ciudad"] = "Chicago"
    df["estado"] = "IL"
    df["pais"] = "USA"
    df["codigo_postal"] = "606" + (seeds % 50).astype(int).astype(str).str.zfill(2)
    df["nombre_sector"] = "Sector " + (1 + (seeds % 99)).astype(int).astype(str)
    return df


def enrich_dim_violencia_domestica(df: pd.DataFrame) -> pd.DataFrame:
    df = _add_legacy_id(df.copy())
    val = df["domestic"].astype(str).str.lower()
    is_dom = val.isin(("true", "1", "yes", "y"))
    seeds = _hash_series("dom|" + val)
    df["descripcion_domestico"] = np.where(
        is_dom, "Incidente doméstico reportado", "No doméstico"
    )
    df["tipo_relacion_victima"] = np.where(
        is_dom,
        _pick_series(("Pareja", "Familiar", "Ex pareja", "Conviviente"), val),
        "N/A",
    )
    df["hubo_orden_restriccion"] = is_dom & (seeds % 4 == 0)
    df["victima_menor_edad"] = is_dom & (seeds % 9 == 0)
    df["intervencion_social"] = is_dom & (seeds % 3 == 0)
    df["reincidencia"] = is_dom & (seeds % 5 == 0)
    return df


def enrich_dim_actualizacion(df: pd.DataFrame) -> pd.DataFrame:
    df = _add_legacy_id(df.copy())
    parsed = _parse_datetime(df["updated_on"])
    df["updated_year"] = parsed.dt.year
    df["updated_month"] = parsed.dt.month
    df["updated_day"] = parsed.dt.day
    df["usuario_actualizador"] = df["updated_on"].astype(str).map(
        lambda s: f"user_{100 + (_seed('act', s) % 900)}"
    )
    df["sistema_origen"] = df["updated_on"].astype(str).map(
        lambda s: _pick(("CPD Portal", "Auto Sync", "FBI Feed", "Manual Entry"), s)
    )
    df["motivo_actualizacion"] = df["updated_on"].astype(str).map(
        lambda s: _pick(
            ("Actualización rutinaria", "Corrección de datos", "Revisión judicial", "Cierre de caso"),
            s,
        )
    )
    df["version_registro"] = df["updated_on"].astype(str).map(lambda s: 1 + (_seed("ver", s) % 5))
    return df


ENRICHERS = {
    "dim_actualizacion": enrich_dim_actualizacion,
    "dim_area_administrativa": enrich_dim_area_administrativa,
    "dim_arresto": enrich_dim_arresto,
    "dim_caso": enrich_dim_caso,
    "dim_distrito_policial": enrich_dim_distrito_policial,
    "dim_tiempo": enrich_dim_tiempo,
    "dim_tipo_crimen": enrich_dim_tipo_crimen,
    "dim_ubicacion_geografica": enrich_dim_ubicacion_geografica,
    "dim_ubicacion_lugar": enrich_dim_ubicacion_lugar,
    "dim_violencia_domestica": enrich_dim_violencia_domestica,
}


def enrich_all_dimensions(dims: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for name, df in dims.items():
        enricher = ENRICHERS.get(name)
        out[name] = enricher(df) if enricher else _add_legacy_id(df.copy())
    return out
