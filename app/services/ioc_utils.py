import ipaddress
import re
from urllib.parse import urlparse


HASH_PATTERNS = {
    "MD5": re.compile(r"^[a-fA-F0-9]{32}$"),
    "SHA1": re.compile(r"^[a-fA-F0-9]{40}$"),
    "SHA256": re.compile(r"^[a-fA-F0-9]{64}$"),
}
DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)([A-Za-z0-9-]{1,63}\.)+[A-Za-z]{2,63}$"
)


def detect_ioc_type(value: str) -> str:
    normalized = value.strip()
    try:
        ipaddress.ip_address(normalized)
        return "IP"
    except ValueError:
        pass

    parsed = urlparse(normalized)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return "URL"

    for hash_type, pattern in HASH_PATTERNS.items():
        if pattern.match(normalized):
            return hash_type

    if DOMAIN_RE.match(normalized):
        return "Dominio"

    raise ValueError("El IOC no tiene un formato soportado.")


def normalize_ioc(value: str) -> str:
    normalized = value.strip()
    if detect_ioc_type(normalized) in {"MD5", "SHA1", "SHA256"}:
        return normalized.lower()
    return normalized
