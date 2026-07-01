from __future__ import annotations

import re
import socket
from functools import lru_cache

from django.conf import settings

EMAIL_FORMAT_RE = re.compile(
    r"^[a-zA-Z0-9._%+-]+@"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)

KNOWN_EMAIL_DOMAINS: frozenset[str] = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "hotmail.com",
        "hotmail.es",
        "outlook.com",
        "outlook.es",
        "live.com",
        "msn.com",
        "yahoo.com",
        "yahoo.es",
        "ymail.com",
        "icloud.com",
        "me.com",
        "mac.com",
        "protonmail.com",
        "proton.me",
        "pm.me",
        "aol.com",
        "mail.com",
        "zoho.com",
        "gmx.com",
        "gmx.es",
        "gmx.net",
        "yandex.com",
        "yandex.ru",
        "tutanota.com",
        "tuta.io",
        "fastmail.com",
        "hey.com",
        "mail.ru",
        "inbox.ru",
        "list.ru",
        "bk.ru",
        "orange.fr",
        "orange.es",
        "libero.it",
        "web.de",
        "t-online.de",
        "qq.com",
        "163.com",
        "126.com",
        "sina.com",
        "rediffmail.com",
    }
)

DEV_EMAIL_SUFFIXES = ("crimetrack.local",)


def normalize_email(email: str) -> str:
    return str(email or "").strip().lower()


def validate_email_address(email: str) -> str:
    """
    Valida formato y dominio del correo.
    Acepta proveedores conocidos o dominios que resuelvan en DNS.
    """
    normalized = normalize_email(email)
    if not normalized:
        raise ValueError("El correo electrónico es obligatorio")
    if len(normalized) > 254:
        raise ValueError("El correo electrónico es demasiado largo")
    if not EMAIL_FORMAT_RE.match(normalized):
        raise ValueError(
            "Formato de correo inválido. Usa un dominio real, por ejemplo "
            "usuario@gmail.com o usuario@empresa.com"
        )

    local, domain = normalized.rsplit("@", 1)
    if len(local) > 64:
        raise ValueError("La parte local del correo es demasiado larga")
    if ".." in local or local.startswith(".") or local.endswith("."):
        raise ValueError("Formato de correo inválido")

    tld = domain.rsplit(".", 1)[-1]
    if len(tld) < 2 or not tld.isalpha():
        raise ValueError(
            "El dominio del correo no es válido. Ejemplos: gmail.com, hotmail.com, outlook.com"
        )

    if domain in KNOWN_EMAIL_DOMAINS:
        return normalized

    if settings.DEBUG and any(domain.endswith(suffix) for suffix in DEV_EMAIL_SUFFIXES):
        return normalized

    if not _domain_resolves(domain):
        raise ValueError(
            f"El dominio «{domain}» no parece existir o no acepta correo. "
            "Verifica que esté escrito correctamente (gmail.com, hotmail.com, etc.)."
        )

    return normalized


@lru_cache(maxsize=256)
def _domain_resolves(domain: str) -> bool:
    try:
        prev = socket.getdefaulttimeout()
        socket.setdefaulttimeout(3.0)
        try:
            socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)
            return True
        finally:
            socket.setdefaulttimeout(prev)
    except OSError:
        return False
