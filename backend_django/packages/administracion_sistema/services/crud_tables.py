from __future__ import annotations

from typing import Any

import pandas as pd

from packages.administracion_sistema.storage import AdminMinioStore


class TableCrudService:
    """CRUD genérico sobre tablas admin en MinIO."""

    def __init__(self, table: str) -> None:
        self.table = table
        self.store = AdminMinioStore()

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        try:
            if pd.isna(value):
                return None
        except Exception:
            pass
        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                return value
        return value

    def _normalize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        return {k: self._normalize_value(v) for k, v in row.items()}

    def list_all(self) -> list[dict[str, Any]]:
        df = self.store.read_table(self.table)
        rows = df.to_dict(orient="records")
        return [self._normalize_row(r) for r in rows]

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        row = self.store.append_row(self.table, data)
        return self._normalize_row(row)

    def update(self, row_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        clean = {k: v for k, v in data.items() if v is not None}
        row = self.store.update_row(self.table, row_id, clean)
        if not row:
            return None
        return self._normalize_row(row)

    def delete(self, row_id: int) -> bool:
        return self.store.delete_row(self.table, row_id)
