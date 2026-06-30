import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models
from app.database import get_db
from app.services.ioc_utils import detect_ioc_type, normalize_ioc
from app.services.risk_engine import classify_score


router = APIRouter(tags=["cases"])


@router.get("/casos", response_class=HTMLResponse)
def cases_page(request: Request, q: str = "", status: str = "", db: Session = Depends(get_db)) -> HTMLResponse:
    statement = select(models.Case).options(selectinload(models.Case.ioc_links).selectinload(models.CaseIOC.ioc))
    if q:
        statement = statement.where(
            models.Case.name.ilike(f"%{q.strip()}%") | models.Case.description.ilike(f"%{q.strip()}%")
        )
    if status:
        statement = statement.where(models.Case.status == status)
    cases = db.scalars(statement.order_by(models.Case.created_at.desc())).all()
    iocs = db.scalars(select(models.IOC).order_by(models.IOC.created_at.desc()).limit(50)).all()
    case_ids = [case.id for case in cases]
    events = []
    if case_ids:
        events = db.scalars(
            select(models.CaseEvent)
            .options(selectinload(models.CaseEvent.ioc))
            .where(models.CaseEvent.case_id.in_(case_ids))
            .order_by(models.CaseEvent.created_at.desc())
            .limit(80)
        ).all()
    events_by_case: dict[int, list[models.CaseEvent]] = {}
    for event in events:
        events_by_case.setdefault(event.case_id, []).append(event)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cases.html",
        context={
            "active_page": "casos",
            "cases": cases,
            "iocs": iocs,
            "events_by_case": events_by_case,
            "filters": {"q": q, "status": status},
            "statuses": ["Abierto", "En investigacion", "Cerrado", "Falso positivo"],
        },
    )


@router.post("/casos")
def create_case(
    name: str = Form(...),
    description: str = Form(""),
    status: str = Form("Abierto"),
    analyst_notes: str = Form(""),
    ioc_id: int | None = Form(None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    case = models.Case(
        name=name,
        description=description,
        status=status,
        analyst_notes=analyst_notes,
    )
    db.add(case)
    db.flush()
    db.add(
        models.CaseEvent(
            case_id=case.id,
            event_type="Caso",
            title="Caso creado",
            description=description,
            analyst="Analista SOC",
        )
    )
    if ioc_id:
        db.add(models.CaseIOC(case_id=case.id, ioc_id=ioc_id))
        db.add(
            models.CaseEvent(
                case_id=case.id,
                ioc_id=ioc_id,
                event_type="Asociacion IOC",
                title="IOC asociado al caso",
                description="IOC existente vinculado durante la creacion del caso.",
                analyst="Analista SOC",
            )
        )
    db.commit()
    return RedirectResponse(url="/casos", status_code=303)


@router.post("/casos/ioc-manual")
def register_manual_ioc(
    case_id: int = Form(...),
    ioc_value: str = Form(...),
    risk_score: int = Form(...),
    verdict: str = Form("Malicioso"),
    source: str = Form("Registro manual"),
    evidence: str = Form(""),
    analyst: str = Form("Analista SOC"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    case = db.get(models.Case, case_id)
    if case is None:
        return RedirectResponse(url="/casos", status_code=303)
    try:
        normalized = normalize_ioc(ioc_value)
        ioc_type = detect_ioc_type(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    score = max(0, min(100, int(risk_score)))
    final_verdict = verdict or classify_score(score)
    ioc = models.IOC(ioc_type=ioc_type, ioc_value=normalized, risk_score=score, verdict=final_verdict)
    db.add(ioc)
    db.flush()
    db.add(
        models.ReputationResult(
            ioc_id=ioc.id,
            source=source or "Registro manual",
            result=final_verdict,
            score=score,
            raw_json=json.dumps({"manual": True, "evidence": evidence, "analyst": analyst}, ensure_ascii=False),
        )
    )
    db.add(models.CaseIOC(case_id=case.id, ioc_id=ioc.id))
    db.add(
        models.CaseEvent(
            case_id=case.id,
            ioc_id=ioc.id,
            event_type="IOC manual",
            title=f"IOC {final_verdict} registrado manualmente",
            description=evidence,
            analyst=analyst,
        )
    )
    db.commit()
    return RedirectResponse(url="/casos", status_code=303)


@router.post("/casos/{case_id}/evento")
def add_case_event(
    case_id: int,
    title: str = Form(...),
    description: str = Form(""),
    analyst: str = Form("Analista SOC"),
    ioc_id: int | None = Form(None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if db.get(models.Case, case_id) is None:
        return RedirectResponse(url="/casos", status_code=303)
    db.add(
        models.CaseEvent(
            case_id=case_id,
            ioc_id=ioc_id or None,
            event_type="Nota",
            title=title,
            description=description,
            analyst=analyst,
        )
    )
    db.commit()
    return RedirectResponse(url="/casos", status_code=303)
