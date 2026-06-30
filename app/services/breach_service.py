from datetime import datetime
from urllib.parse import quote

import requests
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.source_config_service import get_source_config


HIBP_SOURCE = "Have I Been Pwned"


def _base_result(status: str, score: int, summary: str, details: list[str]) -> dict:
    return {
        "title": "Verificar cuenta comprometida",
        "status": status,
        "score": score,
        "summary": summary,
        "details": details,
    }


def _format_breach_date(value: str | None) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return datetime.min


def check_email_breaches(db: Session, email: str) -> dict:
    settings = get_settings()
    config = get_source_config(db, HIBP_SOURCE)

    api_url = "https://haveibeenpwned.com/api/v3/"
    api_key = settings.hibp_api_key or ""
    if config:
        api_url = config.api_url or api_url
        api_key = config.api_key or api_key
        if not config.is_enabled:
            return _base_result(
                "Fuente desactivada",
                0,
                f"{HIBP_SOURCE} esta desactivado en Fuentes Integradas.",
                [
                    "Active la fuente para realizar consultas reales de brechas historicas.",
                    "La verificacion no se simula cuando la integracion esta desactivada.",
                ],
            )

    if not api_key:
        return _base_result(
            "API no configurada",
            0,
            f"No se consulto {HIBP_SOURCE} porque falta configurar la API key.",
            [
                "Ingrese la API key autorizada en Fuentes Integradas > Have I Been Pwned.",
                "HIBP exige una llave para consultar brechas asociadas a cuentas de correo.",
                "La herramienta no marca cuentas como limpias o comprometidas sin consultar el proveedor real.",
            ],
        )

    endpoint = f"{api_url.rstrip('/')}/breachedaccount/{quote(email, safe='')}"
    headers = {
        "hibp-api-key": api_key,
        "user-agent": "IOC-Reputation-Center",
    }
    params = {"truncateResponse": "false"}

    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=settings.request_timeout)
    except requests.RequestException as exc:
        return _base_result(
            "Error de conexion",
            0,
            f"No se pudo consultar {HIBP_SOURCE}.",
            [f"Detalle tecnico: {exc}", "Revise conectividad, proxy, DNS o disponibilidad del proveedor."],
        )

    if response.status_code == 404:
        return _base_result(
            "Sin brechas conocidas",
            5,
            f"{email} no aparece en las brechas publicas consultadas por {HIBP_SOURCE}.",
            [
                "Esto no garantiza que la cuenta nunca haya sido expuesta en fuentes privadas o no indexadas.",
                "Mantenga MFA activo y evite reutilizar contrasenas.",
            ],
        )
    if response.status_code in {401, 403}:
        return _base_result(
            "API key invalida",
            0,
            f"{HIBP_SOURCE} rechazo la consulta por credenciales no autorizadas.",
            [
                "Verifique que la API key guardada en Fuentes Integradas sea valida.",
                "Revise que la fuente este activa y que la URL base apunte a https://haveibeenpwned.com/api/v3/.",
            ],
        )
    if response.status_code == 429:
        return _base_result(
            "Limite excedido",
            0,
            f"{HIBP_SOURCE} aplico rate limit a la API key configurada.",
            [
                "Espere unos minutos antes de repetir la consulta.",
                "Considere controlar el volumen de consultas si varios usuarios usan la herramienta.",
            ],
        )

    try:
        response.raise_for_status()
        breaches = response.json()
    except (requests.RequestException, ValueError) as exc:
        return _base_result(
            "Respuesta no valida",
            0,
            f"{HIBP_SOURCE} devolvio una respuesta que no se pudo procesar.",
            [f"Detalle tecnico: {exc}"],
        )

    if not isinstance(breaches, list):
        return _base_result(
            "Respuesta no valida",
            0,
            f"{HIBP_SOURCE} no devolvio una lista de brechas.",
            ["Revise la URL base configurada para la fuente."],
        )

    breach_count = len(breaches)
    latest = max((_format_breach_date(item.get("BreachDate")) for item in breaches if isinstance(item, dict)), default=datetime.min)
    latest_text = latest.strftime("%d/%m/%Y") if latest != datetime.min else "fecha no disponible"
    details = [
        f"Brechas encontradas: {breach_count}.",
        f"Fecha mas reciente detectada: {latest_text}.",
    ]
    for breach in breaches[:8]:
        if not isinstance(breach, dict):
            continue
        name = breach.get("Title") or breach.get("Name") or "Brecha sin nombre"
        date = breach.get("BreachDate") or "sin fecha"
        classes = ", ".join(breach.get("DataClasses") or []) or "datos no especificados"
        details.append(f"{name} ({date}): {classes}.")
    if breach_count > 8:
        details.append(f"Se omitieron {breach_count - 8} brechas adicionales para mantener el reporte legible.")

    return _base_result(
        "Comprometida",
        min(100, 55 + breach_count * 5),
        f"{email} aparece en brechas historicas consultadas por {HIBP_SOURCE}.",
        details,
    )


def check_phone_breaches(phone: str) -> dict:
    return {
        "title": "Verificar numero comprometido",
        "status": "Proveedor requerido",
        "score": 0,
        "summary": f"{phone} tiene formato valido, pero no se consulto una fuente real de telefonos.",
        "details": [
            "Have I Been Pwned no ofrece verificacion general de numeros telefonicos como endpoint publico equivalente al de correo.",
            "Para hacerlo real se debe integrar un proveedor autorizado que permita busqueda por telefono.",
            "La herramienta no genera resultados simulados para numeros telefonicos.",
        ],
    }
