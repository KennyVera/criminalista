from __future__ import annotations

from typing import Any

import httpx
from django.conf import settings


class PocketBaseError(Exception):
    def __init__(self, message: str, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class PocketBaseClient:
    """Cliente REST para PocketBase (auth admin + colecciones + registros)."""

    def __init__(self, base_url: str | None = None, token: str | None = None):
        self.base_url = (base_url or settings.POCKETBASE_URL).rstrip("/")
        self.token = token
        self._client = httpx.Client(base_url=self.base_url, timeout=120.0)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> PocketBaseClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    @property
    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = self.token
        return headers

    def _handle(self, response: httpx.Response) -> Any:
        if response.is_success:
            if response.status_code == 204:
                return None
            return response.json()
        try:
            payload = response.json()
        except Exception:
            payload = response.text
        message = payload
        if isinstance(payload, dict):
            message = payload.get("message", payload)
        raise PocketBaseError(str(message), response.status_code, payload)

    def auth_admin(self, email: str | None = None, password: str | None = None) -> str:
        email = email or settings.POCKETBASE_ADMIN_EMAIL
        password = password or settings.POCKETBASE_ADMIN_PASSWORD
        if not password:
            raise PocketBaseError(
                "POCKETBASE_ADMIN_PASSWORD vacío. Configúralo en backend_django/.env "
                "(y reinicia el contenedor celery-worker).",
                401,
                None,
            )
        data = self._handle(
            self._client.post(
                "/api/collections/_superusers/auth-with-password",
                json={"identity": email, "password": password},
            )
        )
        self.token = data["token"]
        return self.token

    def health(self) -> bool:
        try:
            response = self._client.get("/api/health")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def list_collections(self) -> list[dict]:
        data = self._handle(self._client.get("/api/collections", headers=self.headers))
        return data.get("items", data) if isinstance(data, dict) else data

    def get_collection_by_name(self, name: str) -> dict | None:
        for collection in self.list_collections():
            if collection.get("name") == name:
                return collection
        return None

    def create_collection(self, body: dict) -> dict:
        return self._handle(
            self._client.post("/api/collections", headers=self.headers, json=body)
        )

    def delete_collection(self, collection_id: str) -> None:
        self._handle(
            self._client.delete(
                f"/api/collections/{collection_id}",
                headers=self.headers,
            )
        )

    def create_record(self, collection: str, body: dict) -> dict:
        return self._handle(
            self._client.post(
                f"/api/collections/{collection}/records",
                headers=self.headers,
                json=body,
            )
        )

    def create_records_batch(
        self,
        collection: str,
        bodies: list[dict],
    ) -> tuple[int, int, list[dict]]:
        """
        Inserta varios registros. Usa /api/batches si existe (PB >= 0.23);
        si no, inserción secuencial con el mismo cliente autenticado.
        """
        if not bodies:
            return 0, 0, []

        response = self._client.post(
            "/api/batches",
            headers=self.headers,
            json={
                "requests": [
                    {
                        "method": "POST",
                        "url": f"/api/collections/{collection}/records",
                        "body": body,
                    }
                    for body in bodies
                ]
            },
        )
        if response.status_code == 404:
            return self._create_records_sequential(collection, bodies)

        data = self._handle(response)
        results = data if isinstance(data, list) else data.get("results", data)
        created = 0
        errors = 0
        samples: list[dict] = []
        for i, item in enumerate(results):
            status_code = int(item.get("status", 500))
            if 200 <= status_code < 300:
                created += 1
                body = item.get("body") or {}
                if len(samples) < 8:
                    samples.append({**bodies[i], "pb_id": body.get("id")})
            else:
                errors += 1
        return created, errors, samples

    def _create_records_sequential(
        self,
        collection: str,
        bodies: list[dict],
    ) -> tuple[int, int, list[dict]]:
        created = 0
        errors = 0
        samples: list[dict] = []
        for body in bodies:
            try:
                record = self.create_record(collection, body)
                created += 1
                if len(samples) < 8:
                    samples.append({**body, "pb_id": record.get("id")})
            except PocketBaseError:
                errors += 1
        return created, errors, samples

    def get_record(self, collection: str, record_id: str, *, expand: str | None = None) -> dict:
        params = {}
        if expand:
            params["expand"] = expand
        return self._handle(
            self._client.get(
                f"/api/collections/{collection}/records/{record_id}",
                headers=self.headers,
                params=params,
            )
        )

    def update_record(self, collection: str, record_id: str, body: dict) -> dict:
        return self._handle(
            self._client.patch(
                f"/api/collections/{collection}/records/{record_id}",
                headers=self.headers,
                json=body,
            )
        )

    def delete_record(self, collection: str, record_id: str) -> None:
        self._handle(
            self._client.delete(
                f"/api/collections/{collection}/records/{record_id}",
                headers=self.headers,
            )
        )

    def count_records(self, collection: str, filter_query: str | None = None) -> int:
        data = self.list_records(collection, page=1, per_page=1, filter_query=filter_query)
        return int(data.get("totalItems", 0))

    def list_records(
        self,
        collection: str,
        *,
        page: int = 1,
        per_page: int = 30,
        sort: str = "-@rowid",
        filter_query: str | None = None,
        expand: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"page": page, "perPage": per_page, "sort": sort}
        if filter_query:
            params["filter"] = filter_query
        if expand:
            params["expand"] = expand
        return self._handle(
            self._client.get(
                f"/api/collections/{collection}/records",
                headers=self.headers,
                params=params,
            )
        )


def get_pocketbase_client(*, authenticate: bool = True) -> PocketBaseClient:
    client = PocketBaseClient()
    if authenticate:
        client.auth_admin()
    return client
