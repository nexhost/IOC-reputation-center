from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app import models
from app.database import get_db
from app.schemas import IOCQuery, IOCResponse
from app.services.ioc_service import query_ioc


router = APIRouter(tags=["ioc"])
PAGE_SIZE = 10
IOC_TYPES = ["IP", "Dominio", "URL", "MD5", "SHA1", "SHA256"]


def _filtered_ioc_query(q: str = "", ioc_type: str = "", verdict: str = ""):
    statement = select(models.IOC).options(selectinload(models.IOC.results))
    if q:
        statement = statement.where(models.IOC.ioc_value.ilike(f"%{q.strip()}%"))
    if ioc_type:
        if ioc_type == "Hash":
            statement = statement.where(models.IOC.ioc_type.in_(["MD5", "SHA1", "SHA256"]))
        else:
            statement = statement.where(models.IOC.ioc_type == ioc_type)
    if verdict:
        statement = statement.where(models.IOC.verdict == verdict)
    return statement


def _paginate(db: Session, statement, page: int, page_size: int = PAGE_SIZE):
    page = max(1, page)
    count_statement = select(func.count()).select_from(statement.order_by(None).subquery())
    total = db.scalar(count_statement) or 0
    pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, pages)
    items = db.scalars(
        statement.order_by(models.IOC.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return items, {"page": page, "pages": pages, "total": total, "page_size": page_size}


@router.get("/consulta", response_class=HTMLResponse)
def search_page(
    request: Request,
    q: str = "",
    ioc_type: str = "",
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    latest_iocs, pagination = _paginate(db, _filtered_ioc_query(q=q, ioc_type=ioc_type), page)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "active_page": "consulta",
            "latest_iocs": latest_iocs,
            "result": None,
            "pagination": pagination,
            "filters": {"q": q, "ioc_type": ioc_type},
            "ioc_types": IOC_TYPES,
        },
    )


@router.post("/consulta", response_class=HTMLResponse)
def search_ioc(
    request: Request,
    ioc_value: str = Form(...),
    analyst: str = Form("Analista SOC"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    try:
        result = query_ioc(db, ioc_value, analyst)
    except ValueError as exc:
        latest_iocs, pagination = _paginate(db, _filtered_ioc_query(), 1)
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="search.html",
            context={
                "active_page": "consulta",
                "latest_iocs": latest_iocs,
                "result": None,
                "error": str(exc),
                "pagination": pagination,
                "filters": {"q": "", "ioc_type": ""},
                "ioc_types": IOC_TYPES,
            },
            status_code=400,
        )

    ioc = db.get(models.IOC, result.id, options=[selectinload(models.IOC.results)])
    latest_iocs, pagination = _paginate(db, _filtered_ioc_query(), 1)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "active_page": "consulta",
            "latest_iocs": latest_iocs,
            "result": ioc,
            "pagination": pagination,
            "filters": {"q": "", "ioc_type": ""},
            "ioc_types": IOC_TYPES,
        },
    )


@router.post("/api/ioc", response_model=IOCResponse)
def api_search_ioc(payload: IOCQuery, db: Session = Depends(get_db)) -> IOCResponse:
    try:
        return query_ioc(db, payload.value, payload.analyst)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/historial", response_class=HTMLResponse)
def history(
    request: Request,
    q: str = "",
    ioc_type: str = "",
    verdict: str = "",
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    iocs, pagination = _paginate(db, _filtered_ioc_query(q=q, ioc_type=ioc_type, verdict=verdict), page)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "active_page": "historial",
            "iocs": iocs,
            "pagination": pagination,
            "filters": {"q": q, "ioc_type": ioc_type, "verdict": verdict},
            "ioc_types": IOC_TYPES,
            "verdicts": ["Bajo", "Moderado", "Alto", "Critico", "Malicioso"],
        },
    )


@router.post("/historial/{ioc_id}/eliminar")
def delete_history(ioc_id: int, db: Session = Depends(get_db)) -> RedirectResponse:
    ioc = db.get(models.IOC, ioc_id)
    if ioc is None:
        raise HTTPException(status_code=404, detail="IOC no encontrado")
    db.query(models.CaseEvent).filter(models.CaseEvent.ioc_id == ioc_id).update({"ioc_id": None})
    db.query(models.CaseIOC).filter(models.CaseIOC.ioc_id == ioc_id).delete()
    db.query(models.ReputationResult).filter(models.ReputationResult.ioc_id == ioc_id).delete()
    db.delete(ioc)
    db.commit()
    return RedirectResponse(url="/historial", status_code=303)


@router.post("/ioc/{ioc_id}/case")
def create_case_from_ioc(ioc_id: int, db: Session = Depends(get_db)) -> RedirectResponse:
    ioc = db.get(models.IOC, ioc_id)
    if ioc is None:
        raise HTTPException(status_code=404, detail="IOC no encontrado")
    case = models.Case(
        name=f"Caso IOC {ioc.ioc_value[:48]}",
        description=f"Caso creado desde consulta de {ioc.ioc_type}.",
        status="Abierto",
    )
    db.add(case)
    db.flush()
    db.add(models.CaseIOC(case_id=case.id, ioc_id=ioc.id))
    db.commit()
    return RedirectResponse(url="/casos", status_code=303)
