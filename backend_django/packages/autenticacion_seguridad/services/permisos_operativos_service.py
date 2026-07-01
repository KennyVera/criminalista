"""Permisos RBAC en capa operativa (app_permisos / app_rol_permisos)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

# (codigo, nombre, modulo, descripcion)
DEFAULT_APP_PERMISOS: list[tuple[str, str, str, str]] = [
    ("dashboard.ver", "Ver dashboard", "dashboard", "Acceso al panel ejecutivo"),
    ("incidentes.crear", "Crear incidente", "despacho", "Registrar incidentes operativos"),
    ("patrullas.asignar", "Asignar patrulla", "despacho", "Conformar y asignar patrullas"),
    ("casos.cerrar", "Cerrar caso", "investigaciones", "Cerrar casos operativos"),
    ("auditoria.exportar", "Exportar auditoría", "auditoria", "Exportar logs de auditoría"),
    ("usuarios.gestionar", "Gestionar usuarios", "admin", "Registrar y editar usuarios"),
    ("permisos.gestionar", "Gestionar permisos", "admin", "Asignar permisos por rol"),
    ("evidencias.gestionar", "Gestionar evidencias", "evidencias", "Subir y custodiar archivos"),
    ("asignaciones.gestionar", "Gestionar asignaciones", "investigaciones", "Asignar detectives"),
    ("expedientes.gestionar", "Gestionar expedientes", "expedientes", "Crear y editar expedientes"),
    ("personal.gestionar", "Gestionar personal policial", "organizacion", "Altas de personal operativo"),
    ("organizacion.gestionar", "Gestionar estructura policial", "organizacion", "Departamentos y distritos"),
]

DEFAULT_ROL_PERMISOS: dict[int, list[str]] = {
    1: [p[0] for p in DEFAULT_APP_PERMISOS],
    2: [
        "dashboard.ver",
        "incidentes.crear",
        "patrullas.asignar",
        "casos.cerrar",
        "asignaciones.gestionar",
        "expedientes.gestionar",
        "evidencias.gestionar",
    ],
    3: [
        "dashboard.ver",
        "asignaciones.gestionar",
        "expedientes.gestionar",
        "evidencias.gestionar",
        "casos.cerrar",
    ],
    4: ["dashboard.ver", "incidentes.crear"],
    5: ["dashboard.ver", "auditoria.exportar"],
}


class PermisosOperativosService:
    def __init__(self, store: TransactionalMinioStore | None = None) -> None:
        self.tx = store or TransactionalMinioStore()
        self.tx.ensure_tables()

    def list_permisos(self, *, activo_only: bool = True) -> list[dict[str, Any]]:
        df = self.tx.read_table("app_permisos")
        if activo_only and not df.empty and "activo" in df.columns:
            df = df[df["activo"].astype(str).str.lower().isin(("true", "1", "si", "sí", "activo"))]
        return df.to_dict(orient="records")

    def get_permiso_by_codigo(self, codigo: str) -> dict[str, Any] | None:
        df = self.tx.read_table("app_permisos")
        if df.empty:
            return None
        hits = df[df["codigo"].astype(str) == codigo.strip()]
        return hits.iloc[0].to_dict() if not hits.empty else None

    def list_rol_permisos(self, fk_rol: int) -> list[str]:
        df = self.tx.read_table("app_rol_permisos")
        if df.empty:
            return []
        mask = pd.to_numeric(df["fk_rol"], errors="coerce") == int(fk_rol)
        return df.loc[mask, "codigo_permiso"].astype(str).tolist()

    def set_rol_permisos(self, fk_rol: int, codigos: list[str]) -> list[str]:
        permisos = self.tx.read_table("app_permisos")
        if permisos.empty:
            raise ValueError("No hay permisos definidos. Ejecute la semilla de seguridad.")

        code_to_id = {
            str(r.codigo): int(r.id_permiso)
            for r in permisos.itertuples(index=False)
            if str(getattr(r, "codigo", "")).strip()
        }
        cleaned = []
        for c in codigos:
            code = str(c).strip()
            if code and code in code_to_id:
                cleaned.append(code)
        cleaned = list(dict.fromkeys(cleaned))

        rel = self.tx.read_table("app_rol_permisos")
        rel = rel[pd.to_numeric(rel["fk_rol"], errors="coerce") != int(fk_rol)] if not rel.empty else rel

        now = utc_now_iso()
        rows = []
        next_id = int(rel["id_rol_permiso"].max()) + 1 if not rel.empty else 1
        for code in cleaned:
            rows.append(
                {
                    "id_rol_permiso": next_id,
                    "fk_rol": int(fk_rol),
                    "fk_permiso": code_to_id[code],
                    "codigo_permiso": code,
                    "fecha_asignacion": now,
                }
            )
            next_id += 1
        if rows:
            rel = pd.concat([rel, pd.DataFrame(rows)], ignore_index=True)
        self.tx.write_table("app_rol_permisos", rel)
        return cleaned

    def user_has_perm(self, fk_rol: int, codigo: str) -> bool:
        return codigo.strip() in self.list_rol_permisos(fk_rol)

    def seed_defaults(self, *, reset_relations: bool = False) -> dict[str, int]:
        permisos = pd.DataFrame(
            [
                {
                    "id_permiso": i + 1,
                    "codigo": c,
                    "nombre": n,
                    "modulo": m,
                    "descripcion": d,
                    "activo": True,
                }
                for i, (c, n, m, d) in enumerate(DEFAULT_APP_PERMISOS)
            ]
        )
        self.tx.write_table("app_permisos", permisos)

        if reset_relations:
            self.tx.write_table(
                "app_rol_permisos",
                pd.DataFrame(columns=self.tx.read_table("app_rol_permisos").columns),
            )

        rel = self.tx.read_table("app_rol_permisos")
        next_id = int(rel["id_rol_permiso"].max()) + 1 if not rel.empty else 1
        now = utc_now_iso()
        code_to_id = {str(r.codigo): int(r.id_permiso) for r in permisos.itertuples(index=False)}
        new_rows = []
        for fk_rol, codes in DEFAULT_ROL_PERMISOS.items():
            existing = set(self.list_rol_permisos(fk_rol)) if not reset_relations else set()
            for code in codes:
                if code in existing:
                    continue
                new_rows.append(
                    {
                        "id_rol_permiso": next_id,
                        "fk_rol": fk_rol,
                        "fk_permiso": code_to_id[code],
                        "codigo_permiso": code,
                        "fecha_asignacion": now,
                    }
                )
                next_id += 1
        if new_rows:
            rel = pd.concat([rel, pd.DataFrame(new_rows)], ignore_index=True)
            self.tx.write_table("app_rol_permisos", rel)

        return {"permisos": len(permisos), "rol_permisos": len(rel)}
