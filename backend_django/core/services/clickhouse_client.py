"""
ClickHouseService — cliente de bajo nivel para la capa TÁCTICA / ESTRATÉGICA.

REGLAS DE ARQUITECTURA (importante):
  * ClickHouse es SOLO para análisis (lectura OLAP / métricas agregadas).
  * El CRUD operativo NO usa este servicio: la escritura operativa vive en
    MinIO vía TransactionalMinioStore (datasets/transactional/).
  * La carga de datos MinIO -> ClickHouse la realiza Airflow (o el comando
    de management `clickhouse_sync`), nunca el flujo operativo del frontend.

Este módulo encapsula la conexión HTTP a ClickHouse usando `clickhouse-connect`.
Si la librería no está instalada o ClickHouse no responde, los métodos elevan
errores claros para que la capa superior pueda degradar con gracia.
"""

from __future__ import annotations

import os
from typing import Any

try:  # import perezoso: el backend operativo no debe romperse si falta la dep
    import clickhouse_connect
except Exception:  # pragma: no cover - entorno sin la dependencia
    clickhouse_connect = None


def _setting(name: str, default: str) -> str:
    """Lee primero settings de Django (si está cargado) y cae a os.getenv."""
    try:
        from django.conf import settings

        if settings.configured and hasattr(settings, name):
            return str(getattr(settings, name))
    except Exception:
        pass
    return os.getenv(name, default)


class ClickHouseUnavailable(RuntimeError):
    """ClickHouse no está disponible o falta la dependencia clickhouse-connect."""


class ClickHouseService:
    """
    Conexión y consultas analíticas a ClickHouse.

    Uso:
        ch = ClickHouseService()
        if ch.ping():
            rows = ch.query("SELECT count() FROM fact_crimes")
    """

    def __init__(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
        secure: bool | None = None,
    ) -> None:
        self.host = host or _setting("CLICKHOUSE_HOST", "127.0.0.1")
        self.port = int(port or _setting("CLICKHOUSE_PORT", "8123"))
        self.user = user or _setting("CLICKHOUSE_USER", "crimetrack")
        self.password = password if password is not None else _setting(
            "CLICKHOUSE_PASSWORD", "crimetrack_ch_2026"
        )
        self.database = database or _setting("CLICKHOUSE_DATABASE", "crimetrack_analytics")
        if secure is None:
            secure = _setting("CLICKHOUSE_SECURE", "False").lower() in ("1", "true", "yes")
        self.secure = secure
        self._client = None

    # -- conexión ---------------------------------------------------------
    def _connect(self, database: str):
        return clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            database=database,
            secure=self.secure,
            connect_timeout=5,
            send_receive_timeout=120,
            compress=True,
        )

    def client(self):
        if clickhouse_connect is None:
            raise ClickHouseUnavailable(
                "Falta la dependencia 'clickhouse-connect'. Instala: "
                "pip install clickhouse-connect"
            )
        if self._client is None:
            try:
                self._client = self._connect(self.database)
            except Exception:
                # La base analítica puede no existir aún (primer arranque):
                # se crea conectándose a 'default' y se reintenta.
                admin = self._connect("default")
                admin.command(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                admin.close()
                self._client = self._connect(self.database)
        return self._client

    def ping(self) -> bool:
        try:
            return bool(self.client().ping())
        except Exception:
            return False

    # -- lectura ----------------------------------------------------------
    def query(self, sql: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Devuelve filas como lista de dicts (columnas -> valores)."""
        result = self.client().query(sql, parameters=parameters or {})
        cols = result.column_names
        return [dict(zip(cols, row)) for row in result.result_rows]

    def query_one(self, sql: str, parameters: dict[str, Any] | None = None) -> dict[str, Any] | None:
        rows = self.query(sql, parameters)
        return rows[0] if rows else None

    def scalar(self, sql: str, parameters: dict[str, Any] | None = None) -> Any:
        result = self.client().query(sql, parameters=parameters or {})
        if result.result_rows:
            return result.result_rows[0][0]
        return None

    def query_df(self, sql: str, parameters: dict[str, Any] | None = None):
        return self.client().query_df(sql, parameters=parameters or {})

    # -- escritura (SOLO para el loader analítico / Airflow) --------------
    def command(self, sql: str) -> None:
        """Ejecuta DDL/DML (CREATE, TRUNCATE, ...). No usar en CRUD operativo."""
        self.client().command(sql)

    def insert_df(self, table: str, df, *, database: str | None = None) -> int:
        """Inserta un DataFrame en una tabla analítica. Devuelve filas insertadas."""
        if df is None or len(df) == 0:
            return 0
        self.client().insert_df(table, df, database=database or self.database)
        return len(df)

    def table_counts(self, tables: list[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for t in tables:
            try:
                counts[t] = int(self.scalar(f"SELECT count() FROM {t}") or 0)
            except Exception:
                counts[t] = -1  # tabla inexistente o error
        return counts

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
