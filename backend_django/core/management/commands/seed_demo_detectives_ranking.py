"""
Registra 10 detectives adicionales, asigna casos para demo del ranking real
(Carlos Ramírez #1 con 6 casos; resto 4 casos c/u) y refresca dashboard.
"""

from __future__ import annotations

import pandas as pd
from django.core.management.base import BaseCommand

from packages.asignacion_investigaciones.services.assignment_service import AssignmentService
from packages.asignacion_investigaciones.services.casos_operativos_store import (
    CasosOperativosStore,
)
from packages.autenticacion_seguridad.services.passwords import hash_password
from packages.autenticacion_seguridad.services.seed import (
    DEFAULT_DETECTIVE_EMAIL,
    FK_ROL_COMISARIO,
    FK_ROL_DETECTIVE,
)
from packages.dashboard_analitica.services.detective_ranking_service import (
    detective_ranking_from_assignments,
)
from packages.dashboard_analitica.services.summary_materializer import (
    materialize_dashboard_summary,
)
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

DEFAULT_DETECTIVE_PASSWORD = "Detective2026!"

EXTRA_DETECTIVES = [
    ("Ana", "García", "detective.garcia@crimetrack.local", "CPD-3012"),
    ("Jorge", "Silva", "detective.silva@crimetrack.local", "CPD-3013"),
    ("Patricia", "Vega", "detective.vega@crimetrack.local", "CPD-3014"),
    ("Roberto", "Díaz", "detective.diaz@crimetrack.local", "CPD-3015"),
    ("Elena", "Castro", "detective.castro@crimetrack.local", "CPD-3016"),
    ("Miguel", "Torres", "detective.torres@crimetrack.local", "CPD-3017"),
    ("Sofía", "Herrera", "detective.herrera@crimetrack.local", "CPD-3018"),
    ("Andrés", "Morales", "detective.morales@crimetrack.local", "CPD-3019"),
    ("Laura", "Jiménez", "detective.jimenez@crimetrack.local", "CPD-3020"),
    ("Diego", "Paredes", "detective.paredes@crimetrack.local", "CPD-3021"),
]

RAMIREZ_CASES = 6
OTHERS_CASES_EACH = 4


class Command(BaseCommand):
    help = (
        "Crea 10 detectives demo, asigna casos (Ramírez 6, otros 4 c/u) "
        "y refresca ranking del dashboard."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-assignments",
            action="store_true",
            help="No borrar asignaciones previas (solo añade hasta alcanzar metas).",
        )

    def handle(self, *args, **options):
        tx = TransactionalMinioStore()
        tx.ensure_tables()
        created = self._ensure_extra_detectives(tx)
        if created:
            self.stdout.write(self.style.SUCCESS(f"Detectives creados: {len(created)}"))
            for e in created:
                self.stdout.write(f"  + {e}")

        comisario = self._get_comisario(tx)
        ramirez = self._get_user_by_email(tx, DEFAULT_DETECTIVE_EMAIL)
        if not comisario:
            raise SystemExit("No hay usuario Comisario. Ejecute seed_auth_minio primero.")
        if not ramirez:
            raise SystemExit("No hay Carlos Ramírez (detective@crimetrack.local).")

        if not options["keep_assignments"]:
            self._clear_assignments(tx)
            self.stdout.write("Asignaciones activas reiniciadas para demo.")

        detectives = self._list_detectives(tx)
        others = [d for d in detectives if int(d["id_usuario"]) != int(ramirez["id_usuario"])]

        needed = RAMIREZ_CASES + len(others) * OTHERS_CASES_EACH
        case_ids = self._collect_case_ids(needed)
        if len(case_ids) < needed:
            raise SystemExit(
                f"Solo hay {len(case_ids)} casos disponibles; se necesitan {needed}."
            )

        svc = AssignmentService()
        comisario_row = comisario
        idx = 0

        n_ramirez = self._assign_count(
            svc,
            comisario_row,
            int(ramirez["id_usuario"]),
            RAMIREZ_CASES,
            case_ids,
            idx,
            options["keep_assignments"],
        )
        idx += n_ramirez
        self.stdout.write(f"Carlos Ramírez: {n_ramirez} casos activos (meta {RAMIREZ_CASES})")

        for det in others:
            n = self._assign_count(
                svc,
                comisario_row,
                int(det["id_usuario"]),
                OTHERS_CASES_EACH,
                case_ids,
                idx,
                options["keep_assignments"],
            )
            idx += n
            self.stdout.write(
                f"  {det['nombres']} {det['apellidos']}: {n} casos (meta {OTHERS_CASES_EACH})"
            )

        materialize_dashboard_summary()
        ranking = detective_ranking_from_assignments(limit=12)
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Ranking actualizado (asignaciones reales):"))
        for row in ranking:
            self.stdout.write(
                f"  #{row['rank']} {row['detective']} — "
                f"{row['casos_asignados']} asignados / {row['casos_resueltos']} resueltos"
            )

    @staticmethod
    def _ensure_extra_detectives(tx: TransactionalMinioStore) -> list[str]:
        df = tx.read_table("app_usuarios")
        if df.empty:
            df = pd.DataFrame(columns=tx.read_table("app_usuarios").columns)
        emails = set(df["email"].astype(str).str.lower()) if not df.empty else set()
        next_id = int(df["id_usuario"].max()) + 1 if not df.empty else 1
        created: list[str] = []
        for nombres, apellidos, email, placa in EXTRA_DETECTIVES:
            key = email.lower()
            if key in emails:
                continue
            row = {
                "id_usuario": next_id,
                "fk_rol": FK_ROL_DETECTIVE,
                "numero_placa": placa,
                "nombres": nombres,
                "apellidos": apellidos,
                "email": key,
                "password_hash": hash_password(DEFAULT_DETECTIVE_PASSWORD),
                "estado_cuenta": "Activa",
                "intentos_login_fallidos": 0,
                "fecha_creacion": utc_now_iso(),
            }
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            emails.add(key)
            created.append(f"{nombres} {apellidos} <{key}>")
            next_id += 1
        if created:
            tx.write_table("app_usuarios", df)
        return created

    @staticmethod
    def _get_comisario(tx: TransactionalMinioStore) -> dict | None:
        df = tx.read_table("app_usuarios")
        if df.empty:
            return None
        mask = df["fk_rol"].astype(int) == FK_ROL_COMISARIO
        if not mask.any():
            return None
        return df[mask].iloc[0].to_dict()

    @staticmethod
    def _get_user_by_email(tx: TransactionalMinioStore, email: str) -> dict | None:
        df = tx.read_table("app_usuarios")
        if df.empty:
            return None
        mask = df["email"].astype(str).str.lower() == email.lower()
        if not mask.any():
            return None
        return df[mask].iloc[0].to_dict()

    @staticmethod
    def _list_detectives(tx: TransactionalMinioStore) -> list[dict]:
        df = tx.read_table("app_usuarios")
        if df.empty:
            return []
        det = df[df["fk_rol"].astype(int) == FK_ROL_DETECTIVE]
        return det.to_dict(orient="records")

    @staticmethod
    def _clear_assignments(tx: TransactionalMinioStore) -> None:
        from packages.shared.minio_transactional import SCHEMAS

        tx.write_table("app_asignaciones", pd.DataFrame(columns=SCHEMAS["app_asignaciones"]))

    @staticmethod
    def _collect_case_ids(needed: int) -> list[int]:
        store = CasosOperativosStore()
        ids: list[int] = []
        page = 1
        while len(ids) < needed:
            res = store.search_casos(solo_sin_asignar=True, page=page, per_page=100)
            for item in res.get("items") or []:
                ids.append(int(item["id"]))
            total_pages = int(res.get("totalPages") or 1)
            if page >= total_pages:
                break
            page += 1
        return ids[:needed]

    @staticmethod
    def _active_count_for_detective(fk_detective: int) -> int:
        tx = TransactionalMinioStore()
        df = tx.read_table("app_asignaciones")
        if df.empty:
            return 0
        mask = (df["fk_detective"].astype(int) == fk_detective) & (
            df["estado_asignacion"].astype(str) == "Activa"
        )
        return int(mask.sum())

    def _assign_count(
        self,
        svc: AssignmentService,
        comisario: dict,
        fk_detective: int,
        target: int,
        case_ids: list[int],
        start_idx: int,
        keep: bool,
    ) -> int:
        current = self._active_count_for_detective(fk_detective) if keep else 0
        to_assign = max(0, target - current)
        for i in range(to_assign):
            if start_idx + i >= len(case_ids):
                break
            fk_caso = case_ids[start_idx + i]
            try:
                svc.assign_detective(
                    fk_caso=fk_caso,
                    fk_detective=fk_detective,
                    comisario=comisario,
                    observaciones="Demo ranking dashboard — asignación automática",
                )
            except Exception as exc:
                self.stderr.write(f"  aviso caso {fk_caso}: {exc}")
        return self._active_count_for_detective(fk_detective)
