from __future__ import annotations

from typing import Any

import pandas as pd

from packages.administracion_sistema.storage import AdminMinioStore


class PermissionsAdminService:
    def __init__(self) -> None:
        self.store = AdminMinioStore()

    def list_permisos(self) -> list[dict]:
        return self.store.read_table("sys_permisos").to_dict(orient="records")

    def get_role_permissions(self, fk_rol: int) -> dict[str, Any]:
        df = self.store.read_table("sys_rol_permisos")
        codes = df[df["fk_rol"] == fk_rol]["codigo_permiso"].astype(str).tolist()
        all_perms = self.list_permisos()
        return {
            "fk_rol": fk_rol,
            "codigos": codes,
            "permisos": [p for p in all_perms if p["codigo"] in codes],
        }

    def set_role_permissions(self, fk_rol: int, codigos: list[str]) -> dict[str, Any]:
        df = self.store.read_table("sys_rol_permisos")
        df = df[df["fk_rol"] != fk_rol]
        next_id = int(df["id"].max()) + 1 if len(df) else 1
        rows = []
        for code in codigos:
            rows.append({"id": next_id, "fk_rol": fk_rol, "codigo_permiso": code})
            next_id += 1
        if rows:
            df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
        self.store.write_table("sys_rol_permisos", df)
        return self.get_role_permissions(fk_rol)
