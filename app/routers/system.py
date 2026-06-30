from collections import Counter

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models
from app.config import get_settings
from app.database import get_db
from app.services.dashboard_service import get_dashboard_context
from app.services.ioc_service import query_ioc
from app.services.document_service import DOCUMENTS, generate_document
from app.services.source_config_service import list_source_configs, mask_key, update_source_config


router = APIRouter(tags=["system"])


@router.get("/fuentes", response_class=HTMLResponse)
def sources_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    context = get_dashboard_context(db)
    settings = get_settings()
    configs = list_source_configs(db)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="sources.html",
        context={
            "active_page": "fuentes",
            "source_health": context["source_health"],
            "settings": settings,
            "configs": configs,
            "mask_key": mask_key,
            "lookup_result": None,
            "error": None,
        },
    )


@router.post("/fuentes/configurar")
def configure_source(
    source: str = Form(...),
    api_url: str = Form(...),
    api_key: str = Form(""),
    is_enabled: str | None = Form(None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    update_source_config(db, source=source, api_url=api_url, api_key=api_key, is_enabled=is_enabled == "on")
    return RedirectResponse(url="/fuentes", status_code=303)


@router.post("/fuentes/consulta", response_class=HTMLResponse)
def sources_lookup(
    request: Request,
    ioc_value: str = Form(...),
    analyst: str = Form("Analista SOC"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    context = get_dashboard_context(db)
    settings = get_settings()
    configs = list_source_configs(db)
    try:
        result = query_ioc(db, ioc_value, analyst)
    except ValueError as exc:
        result = None
        error = str(exc)
    else:
        error = None
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="sources.html",
        context={
            "active_page": "fuentes",
            "source_health": context["source_health"],
            "settings": settings,
            "configs": configs,
            "mask_key": mask_key,
            "lookup_result": result,
            "error": error,
        },
    )


@router.get("/alertas", response_class=HTMLResponse)
def alerts_page(
    request: Request,
    q: str = "",
    ioc_type: str = "",
    level: str = "",
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    page_size = 10
    statement = select(models.IOC).where(models.IOC.risk_score >= 21)
    if q:
        statement = statement.where(models.IOC.ioc_value.ilike(f"%{q.strip()}%"))
    if ioc_type:
        if ioc_type == "Hash":
            statement = statement.where(models.IOC.ioc_type.in_(["MD5", "SHA1", "SHA256"]))
        else:
            statement = statement.where(models.IOC.ioc_type == ioc_type)
    if level:
        statement = statement.where(models.IOC.verdict == level)
    total = db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
    pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, pages)
    risky_iocs = db.scalars(
        statement.order_by(models.IOC.risk_score.desc(), models.IOC.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    all_alerts = db.scalars(select(models.IOC).where(models.IOC.risk_score >= 21)).all()
    level_counts = Counter(ioc.verdict for ioc in all_alerts)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="alerts.html",
        context={
            "active_page": "alertas",
            "risky_iocs": risky_iocs,
            "pagination": {"page": page, "pages": pages, "total": total},
            "filters": {"q": q, "ioc_type": ioc_type, "level": level},
            "ioc_types": ["IP", "Dominio", "URL", "Hash"],
            "levels": ["Moderado", "Alto", "Critico", "Malicioso"],
            "level_counts": {
                "Moderado": level_counts["Moderado"],
                "Alto": level_counts["Alto"],
                "Critico": level_counts["Critico"],
                "Malicioso": level_counts["Malicioso"],
            },
        },
    )


@router.get("/configuracion", response_class=HTMLResponse)
def settings_page(request: Request) -> HTMLResponse:
    settings = get_settings()
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={"active_page": "configuracion", "settings": settings},
    )


@router.get("/acerca-de", response_class=HTMLResponse)
def about_page(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="about.html",
        context={"active_page": "acerca", "documents": DOCUMENTS},
    )


@router.get("/acerca-de/documentos/{slug}")
def download_document(slug: str) -> FileResponse:
    path = generate_document(slug)
    return FileResponse(path, filename=path.name)
