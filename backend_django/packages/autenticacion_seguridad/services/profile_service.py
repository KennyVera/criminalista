from __future__ import annotations

import mimetypes
import os
import uuid
from typing import Any

import pandas as pd

from core.services.minio_store import MinioParquetStore
from packages.autenticacion_seguridad.services.auth_service import AuthService
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

MAX_BIOGRAFIA = 500


class ProfileService:
    def __init__(self, store: TransactionalMinioStore | None = None) -> None:
        self.store = store or TransactionalMinioStore()
        self.olap = MinioParquetStore()
        self._bucket = os.getenv("MINIO_BUCKET", "crimetrack-evidence")
        self._prefix = os.getenv("MINIO_USER_PROFILE_PREFIX", "usuarios/perfiles")

    def _profiles_df(self) -> pd.DataFrame:
        return self.store.read_table("app_perfiles_usuario")

    def _ensure_profile_row(self, user_id: int) -> pd.DataFrame:
        df = self._profiles_df()
        mask = df["fk_usuario"] == user_id
        if mask.any():
            return df
        row = {
            "fk_usuario": user_id,
            "telefono": "",
            "biografia": "",
            "foto_url": "",
            "actualizado_en": utc_now_iso(),
        }
        self.store.append_row("app_perfiles_usuario", row)
        return self._profiles_df()

    def get_profile(self, user_id: int) -> dict[str, Any] | None:
        auth = AuthService(self.store)
        df = auth._read_users()
        user_row = df[df["id_usuario"] == user_id]
        if user_row.empty:
            return None
        user = user_row.iloc[0].to_dict()
        roles = auth._roles_map()
        prof_df = self._ensure_profile_row(user_id)
        prof = prof_df[prof_df["fk_usuario"] == user_id].iloc[0].to_dict()
        foto_url = str(prof.get("foto_url") or "").strip()
        tiene_foto = bool(foto_url)
        actualizado = prof.get("actualizado_en")
        return {
            "id_usuario": int(user["id_usuario"]),
            "fk_rol": int(user["fk_rol"]),
            "nombre_rol": roles.get(int(user["fk_rol"]), ""),
            "numero_placa": user["numero_placa"],
            "nombres": user["nombres"],
            "apellidos": user["apellidos"],
            "email": user["email"],
            "estado_cuenta": user["estado_cuenta"],
            "telefono": str(prof.get("telefono") or ""),
            "biografia": str(prof.get("biografia") or ""),
            "tiene_foto": tiene_foto,
            "foto_actualizada_en": actualizado if tiene_foto else None,
            "actualizado_en": actualizado,
        }

    def profile_extras(self, user_id: int) -> dict[str, Any]:
        prof_df = self._profiles_df()
        row = prof_df[prof_df["fk_usuario"] == user_id]
        if row.empty:
            return {
                "tiene_foto": False,
                "telefono": "",
                "biografia": "",
                "foto_actualizada_en": None,
            }
        prof = row.iloc[0].to_dict()
        foto_url = str(prof.get("foto_url") or "").strip()
        tiene_foto = bool(foto_url)
        actualizado = prof.get("actualizado_en")
        return {
            "tiene_foto": tiene_foto,
            "telefono": str(prof.get("telefono") or ""),
            "biografia": str(prof.get("biografia") or ""),
            "foto_actualizada_en": actualizado if tiene_foto else None,
        }

    def update_profile(self, user_id: int, data: dict[str, Any]) -> dict[str, Any]:
        users_df = AuthService(self.store)._read_users()
        mask_user = users_df["id_usuario"] == user_id
        if not mask_user.any():
            raise ValueError("Usuario no encontrado")

        if "nombres" in data:
            nombres = str(data["nombres"]).strip()
            if not nombres:
                raise ValueError("Los nombres son obligatorios")
            users_df.loc[mask_user, "nombres"] = nombres
        if "apellidos" in data:
            apellidos = str(data["apellidos"]).strip()
            if not apellidos:
                raise ValueError("Los apellidos son obligatorios")
            users_df.loc[mask_user, "apellidos"] = apellidos
        self.store.write_table("app_usuarios", users_df)

        prof_df = self._ensure_profile_row(user_id)
        mask_prof = prof_df["fk_usuario"] == user_id
        if "telefono" in data:
            prof_df.loc[mask_prof, "telefono"] = str(data["telefono"] or "").strip()[:30]
        if "biografia" in data:
            bio = str(data["biografia"] or "").strip()
            if len(bio) > MAX_BIOGRAFIA:
                raise ValueError(f"La biografía no puede superar {MAX_BIOGRAFIA} caracteres")
            prof_df.loc[mask_prof, "biografia"] = bio
        prof_df.loc[mask_prof, "actualizado_en"] = utc_now_iso()
        self.store.write_table("app_perfiles_usuario", prof_df)
        return self.get_profile(user_id)

    def set_foto(self, user_id: int, *, file_obj: Any, filename: str) -> dict[str, Any]:
        body = file_obj.read()
        if not body:
            raise ValueError("El archivo de imagen está vacío.")
        content_type = (
            getattr(file_obj, "content_type", None)
            or mimetypes.guess_type(filename)[0]
            or ""
        )
        if not str(content_type).startswith("image/"):
            raise ValueError("La foto de perfil debe ser una imagen.")

        safe_name = "".join(c for c in filename if c.isalnum() or c in "._-") or "foto"
        key = f"{self._prefix}/{int(user_id)}/{uuid.uuid4().hex}_{safe_name}"
        self.olap._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body,
            ContentType=content_type or "application/octet-stream",
        )

        prof_df = self._ensure_profile_row(user_id)
        mask = prof_df["fk_usuario"] == user_id
        prof_df.loc[mask, "foto_url"] = f"s3://{self._bucket}/{key}"
        prof_df.loc[mask, "actualizado_en"] = utc_now_iso()
        self.store.write_table("app_perfiles_usuario", prof_df)
        return self.get_profile(user_id)

    def remove_foto(self, user_id: int) -> dict[str, Any]:
        prof_df = self._ensure_profile_row(user_id)
        mask = prof_df["fk_usuario"] == user_id
        prof_df.loc[mask, "foto_url"] = ""
        prof_df.loc[mask, "actualizado_en"] = utc_now_iso()
        self.store.write_table("app_perfiles_usuario", prof_df)
        return self.get_profile(user_id)

    def get_foto(self, user_id: int) -> dict[str, Any] | None:
        prof_df = self._profiles_df()
        row = prof_df[prof_df["fk_usuario"] == user_id]
        if row.empty:
            return None
        url = str(row.iloc[0].get("foto_url") or "").strip()
        if not url:
            return None
        raw = url[len("s3://") :] if url.startswith("s3://") else url
        parts = raw.split("/", 1)
        if len(parts) != 2:
            return None
        bucket, key = parts
        resp = self.olap._client.get_object(Bucket=bucket, Key=key)
        body = resp["Body"].read()
        content_type = resp.get("ContentType") or "image/jpeg"
        return {"body": body, "content_type": content_type}
