"""Helpers para definir campos de colecciones PocketBase v0.38+."""


def text_field(name: str, *, required: bool = False) -> dict:
    return {
        "name": name,
        "type": "text",
        "required": required,
        "presentable": False,
        "options": {"min": None, "max": None, "pattern": ""},
    }


def number_field(name: str, *, required: bool = False, no_decimal: bool = False) -> dict:
    return {
        "name": name,
        "type": "number",
        "required": required,
        "presentable": False,
        "options": {"min": None, "max": None, "noDecimal": no_decimal},
    }


def bool_field(name: str, *, required: bool = False) -> dict:
    return {
        "name": name,
        "type": "bool",
        "required": required,
        "presentable": False,
        "options": {},
    }


def date_field(name: str, *, required: bool = False) -> dict:
    return {
        "name": name,
        "type": "date",
        "required": required,
        "presentable": False,
        "options": {"min": "", "max": ""},
    }


def relation_field(
    name: str,
    collection_id: str,
    *,
    max_select: int = 1,
    cascade_delete: bool = False,
) -> dict:
    # PocketBase 0.38+ espera opciones de relación en el nivel raíz del campo.
    return {
        "name": name,
        "type": "relation",
        "required": False,
        "presentable": False,
        "collectionId": collection_id,
        "cascadeDelete": cascade_delete,
        "minSelect": None,
        "maxSelect": max_select,
        "displayFields": [],
    }
