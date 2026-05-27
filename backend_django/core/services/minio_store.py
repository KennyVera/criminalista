"""
Lectura/escritura de tablas analíticas (dims + fact) en MinIO como Parquet.
PocketBase solo aloja el dataset crudo crimes_220k.
"""

from __future__ import annotations

import io
import os
from typing import Any

import pandas as pd

try:
    import boto3
    from botocore.client import Config
except ImportError:
    boto3 = None

DIM_COLLECTIONS = [
    "dim_actualizacion",
    "dim_area_administrativa",
    "dim_arresto",
    "dim_caso",
    "dim_distrito_policial",
    "dim_tiempo",
    "dim_tipo_crimen",
    "dim_ubicacion_geografica",
    "dim_ubicacion_lugar",
    "dim_violencia_domestica",
]

MINIO_STAR_COLLECTIONS = frozenset([*DIM_COLLECTIONS, "fact_crimes"])
POCKETBASE_ONLY_COLLECTIONS = frozenset(["crimes_220k"])

ALL_DATA_COLLECTIONS = POCKETBASE_ONLY_COLLECTIONS | MINIO_STAR_COLLECTIONS


def is_minio_collection(name: str) -> bool:
    return name in MINIO_STAR_COLLECTIONS


def is_pocketbase_collection(name: str) -> bool:
    return name in POCKETBASE_ONLY_COLLECTIONS


class MinioParquetStore:
    def __init__(self):
        if not boto3:
            raise RuntimeError("Instala boto3: pip install boto3")
        self.endpoint = os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000")
        self.bucket = os.getenv("MINIO_BUCKET", "crimetrack-evidence")
        self.prefix = os.getenv("MINIO_STAR_PREFIX", "datasets/star")
        self._client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=os.getenv("MINIO_ROOT_USER", "minioadmin"),
            aws_secret_access_key=os.getenv(
                "MINIO_ROOT_PASSWORD", "minioadmin_change_me"
            ),
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        self._cache: dict[str, pd.DataFrame] = {}

    def _object_key(self, collection: str) -> str:
        return f"{self.prefix}/{collection}.parquet"

    def fact_crimes_glob(self) -> str:
        """Patron S3/DuckDB para hechos particionados o monolitico."""
        return f"{self.prefix}/fact_crimes/**/*.parquet"

    def fact_crimes_partitioned_prefix(self) -> str:
        return f"{self.prefix}/fact_crimes/"

    def delete_prefix(self, prefix: str) -> int:
        """Elimina todos los objetos bajo un prefijo (paginado)."""
        deleted = 0
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            contents = page.get("Contents", [])
            if not contents:
                continue
            keys = [{"Key": o["Key"]} for o in contents]
            self._client.delete_objects(Bucket=self.bucket, Delete={"Objects": keys})
            deleted += len(keys)
        return deleted

    def has_partitioned_facts(self) -> bool:
        resp = self._client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=self.fact_crimes_partitioned_prefix(),
            MaxKeys=1,
        )
        return bool(resp.get("Contents") or resp.get("KeyCount", 0))

    def invalidate_cache(self, collection: str | None = None) -> None:
        if collection:
            self._cache.pop(collection, None)
        else:
            self._cache.clear()

    def read_df(self, collection: str, *, use_cache: bool = True) -> pd.DataFrame:
        if use_cache and collection in self._cache:
            return self._cache[collection].copy()

        key = self._object_key(collection)
        try:
            obj = self._client.get_object(Bucket=self.bucket, Key=key)
            df = pd.read_parquet(io.BytesIO(obj["Body"].read()))
        except self._client.exceptions.NoSuchKey:
            df = pd.DataFrame()
        except Exception as exc:
            err = str(exc)
            if "NoSuchKey" in err or "404" in err:
                df = pd.DataFrame()
            else:
                raise

        if "id" not in df.columns and len(df) > 0:
            df.insert(0, "id", range(1, len(df) + 1))

        if use_cache:
            self._cache[collection] = df.copy()
        return df

    def write_df(self, collection: str, df: pd.DataFrame) -> None:
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False, compression="snappy")
        buffer.seek(0)
        self._client.put_object(
            Bucket=self.bucket,
            Key=self._object_key(collection),
            Body=buffer.getvalue(),
            ContentType="application/octet-stream",
        )
        self.invalidate_cache(collection)

    def count(self, collection: str) -> int:
        if collection == "fact_crimes" and self.has_partitioned_facts():
            from core.services.analytics_service import AnalyticsService

            return AnalyticsService(self).count_fact_crimes()
        return len(self.read_df(collection))

    def list_records(
        self,
        collection: str,
        *,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        sort: str = "-id",
    ) -> dict[str, Any]:
        if collection == "fact_crimes" and self.has_partitioned_facts():
            return self._list_records_duckdb(
                collection, page=page, per_page=per_page, search=search, sort=sort
            )
        df = self.read_df(collection)
        if df.empty:
            return {"items": [], "page": page, "perPage": per_page, "totalItems": 0, "totalPages": 0}

        if search:
            mask = pd.Series(False, index=df.index)
            for col in df.select_dtypes(include=["object", "string"]).columns:
                mask |= df[col].astype(str).str.contains(search, case=False, na=False)
            df = df[mask]

        ascending = not sort.startswith("-")
        sort_col = sort.lstrip("-@")
        if sort_col in df.columns:
            df = df.sort_values(sort_col, ascending=ascending)
        elif "id" in df.columns:
            df = df.sort_values("id", ascending=ascending)

        total = len(df)
        total_pages = max(1, (total + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        chunk = df.iloc[start : start + per_page]

        items = chunk.to_dict(orient="records")
        for row in items:
            for k, v in row.items():
                if pd.isna(v):
                    row[k] = None
                elif hasattr(v, "item"):
                    try:
                        row[k] = v.item()
                    except Exception:
                        row[k] = v

        return {
            "items": items,
            "page": page,
            "perPage": per_page,
            "totalItems": total,
            "totalPages": total_pages,
        }

    def get_record(self, collection: str, record_id: str) -> dict | None:
        df = self.read_df(collection)
        if df.empty or "id" not in df.columns:
            return None
        rid = int(record_id) if str(record_id).isdigit() else record_id
        match = df[df["id"].astype(str) == str(rid)]
        if match.empty:
            return None
        row = match.iloc[0].to_dict()
        return {k: (None if pd.isna(v) else v) for k, v in row.items()}

    def create_record(self, collection: str, body: dict) -> dict:
        df = self.read_df(collection)
        body = {k: v for k, v in body.items() if v is not None and k != "id"}
        new_id = int(df["id"].max()) + 1 if not df.empty and "id" in df.columns else 1
        body["id"] = new_id
        df = pd.concat([df, pd.DataFrame([body])], ignore_index=True)
        self.write_df(collection, df)
        return body

    def update_record(self, collection: str, record_id: str, body: dict) -> dict:
        df = self.read_df(collection)
        idx = df.index[df["id"].astype(str) == str(record_id)]
        if idx.empty:
            raise KeyError(f"Registro {record_id} no encontrado")
        for k, v in body.items():
            if k != "id":
                df.at[idx[0], k] = v
        self.write_df(collection, df)
        return df.loc[idx[0]].to_dict()

    def delete_record(self, collection: str, record_id: str) -> None:
        df = self.read_df(collection)
        df = df[df["id"].astype(str) != str(record_id)]
        self.write_df(collection, df)

    def _list_records_duckdb(
        self,
        collection: str,
        *,
        page: int,
        per_page: int,
        search: str | None,
        sort: str,
    ) -> dict[str, Any]:
        from core.services.analytics_service import AnalyticsService

        con = AnalyticsService(self).connection()
        src = AnalyticsService(self)._fact_parquet_source()
        order = "DESC" if sort.startswith("-") else "ASC"
        col = sort.lstrip("-@") or "id"
        offset = (max(1, page) - 1) * per_page
        where = ""
        if search:
            where = f" WHERE CAST(id AS VARCHAR) LIKE '%{search.replace(chr(39), '')}%'"
        total = int(
            con.execute(f"SELECT COUNT(*) FROM read_parquet('{src}'){where}").fetchone()[0]
        )
        sql = f"""
            SELECT * FROM read_parquet('{src}')
            {where}
            ORDER BY {col} {order}
            LIMIT {per_page} OFFSET {offset}
        """
        df = con.execute(sql).fetchdf()
        items = df.to_dict(orient="records")
        for row in items:
            for k, v in row.items():
                if pd.isna(v):
                    row[k] = None
        total_pages = max(1, (total + per_page - 1) // per_page)
        return {
            "items": items,
            "page": page,
            "perPage": per_page,
            "totalItems": total,
            "totalPages": total_pages,
        }

    def _id_lookup(self, collection: str) -> dict[int, dict]:
        """Mapa id -> fila para joins en dashboard."""
        df = self.read_df(collection)
        if df.empty or "id" not in df.columns:
            return {}
        lookup: dict[int, dict] = {}
        for _, row in df.iterrows():
            rid = row.get("id")
            if pd.isna(rid):
                continue
            lookup[int(rid)] = {
                k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()
            }
        return lookup

    def enrich_facts_for_dashboard(self, facts: list[dict]) -> list[dict]:
        """Resuelve FKs a etiquetas legibles (Overview: tipo, distrito, año)."""
        if not facts:
            return []

        tipo_by_id = self._id_lookup("dim_tipo_crimen")
        distrito_by_id = self._id_lookup("dim_distrito_policial")
        tiempo_by_id = self._id_lookup("dim_tiempo")

        enriched: list[dict] = []
        for fact in facts:
            row = dict(fact)
            row["legacy_id"] = fact.get("raw_row_id") or fact.get("id")

            def _fk(key: str) -> int | None:
                val = fact.get(key)
                if val is None or val == "" or (isinstance(val, float) and pd.isna(val)):
                    return None
                try:
                    return int(val)
                except (TypeError, ValueError):
                    return None

            tipo = tipo_by_id.get(_fk("fk_tipo_crimen") or -1, {})
            distrito = distrito_by_id.get(_fk("fk_distrito") or -1, {})
            tiempo = tiempo_by_id.get(_fk("fk_tiempo") or -1, {})

            row["expand"] = {
                "tipo_crimen": {
                    "primary_type": tipo.get("primary_type") or tipo.get("description"),
                },
                "distrito": {
                    "district": distrito.get("district"),
                    "beat": distrito.get("beat"),
                },
                "tiempo": {
                    "year": tiempo.get("year"),
                    "date": tiempo.get("date"),
                },
            }
            enriched.append(row)
        return enriched
