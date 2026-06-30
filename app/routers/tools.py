import hashlib
import re

import requests
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.breach_service import check_email_breaches, check_phone_breaches
from app.services.ioc_service import query_ioc


router = APIRouter(tags=["tools"])


def _base_context(result: dict | None = None, error: str | None = None) -> dict:
    return {"active_page": "herramientas", "result": result, "error": error}


@router.get("/herramientas", response_class=HTMLResponse)
def tools_page(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="tools.html",
        context=_base_context(),
    )


@router.post("/herramientas/cuenta", response_class=HTMLResponse)
def check_account(request: Request, account: str = Form(...), db: Session = Depends(get_db)) -> HTMLResponse:
    value = account.strip()
    email_re = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone_re = re.compile(r"^\+?[0-9\s().-]{7,20}$")
    if email_re.match(value):
        result = check_email_breaches(db, value.lower())
    elif phone_re.match(value):
        result = check_phone_breaches(value)
    else:
        result = None
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="tools.html",
            context=_base_context(result, "Ingrese un correo o numero telefonico valido."),
            status_code=400,
        )
    return request.app.state.templates.TemplateResponse(request=request, name="tools.html", context=_base_context(result))


@router.post("/herramientas/password", response_class=HTMLResponse)
def check_password(request: Request, password: str = Form(...)) -> HTMLResponse:
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    count = 0
    try:
        response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=12)
        response.raise_for_status()
        for line in response.text.splitlines():
            candidate, times = line.split(":", 1)
            if candidate == suffix:
                count = int(times)
                break
    except requests.RequestException as exc:
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="tools.html",
            context=_base_context(None, f"No se pudo consultar Pwned Passwords: {exc}"),
            status_code=502,
        )

    compromised = count > 0
    result = {
        "title": "Verificacion de contrasena comprometida",
        "status": "Comprometida" if compromised else "Sin evidencia publica",
        "score": 95 if compromised else 5,
        "summary": (
            f"La contrasena aparece {count:,} veces en filtraciones publicas."
            if compromised
            else "No aparece en la base consultada mediante k-anonymity."
        ),
        "details": [
            "La contrasena completa nunca se envia; solo se consulta el prefijo SHA1.",
            "Si aparece comprometida, cambiela de inmediato y no la reutilice.",
            "Use un gestor de contrasenas y MFA.",
        ],
    }
    return request.app.state.templates.TemplateResponse(request=request, name="tools.html", context=_base_context(result))


@router.post("/herramientas/ip", response_class=HTMLResponse)
def check_ip(request: Request, ip_value: str = Form(...), db: Session = Depends(get_db)) -> HTMLResponse:
    try:
        ioc = query_ioc(db, ip_value, "Herramientas")
    except ValueError as exc:
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="tools.html",
            context=_base_context(None, str(exc)),
            status_code=400,
        )
    result = {
        "title": "Verificacion de IP comprometida",
        "status": ioc.verdict,
        "score": ioc.risk_score,
        "summary": f"{ioc.ioc_value} fue consultada como {ioc.ioc_type}.",
        "details": [f"{source.source}: {source.result} ({source.score}/100)" for source in ioc.source_results],
    }
    return request.app.state.templates.TemplateResponse(request=request, name="tools.html", context=_base_context(result))


@router.post("/herramientas/enlace", response_class=HTMLResponse)
def check_url(request: Request, url_value: str = Form(...), db: Session = Depends(get_db)) -> HTMLResponse:
    try:
        ioc = query_ioc(db, url_value, "Herramientas")
    except ValueError as exc:
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="tools.html",
            context=_base_context(None, str(exc)),
            status_code=400,
        )
    result = {
        "title": "Verificacion de enlace malicioso",
        "status": ioc.verdict,
        "score": ioc.risk_score,
        "summary": f"{ioc.ioc_value} fue consultado contra fuentes configuradas.",
        "details": [f"{source.source}: {source.result} ({source.score}/100)" for source in ioc.source_results],
    }
    return request.app.state.templates.TemplateResponse(request=request, name="tools.html", context=_base_context(result))
