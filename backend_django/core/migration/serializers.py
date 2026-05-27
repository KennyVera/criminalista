from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal


def pg_value_to_pb(value) -> object | None:
    """Convierte tipos de psycopg2 a JSON compatible con PocketBase."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (datetime, date)):
        if isinstance(value, datetime):
            return value.isoformat()
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (int, float, str)):
        return value
    return str(value)
