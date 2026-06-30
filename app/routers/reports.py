from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models
from app.config import get_settings
from app.database import get_db
from app.services.report_service import generate_ioc_report


router = APIRouter(tags=["reports"])
PAGE_SIZE = 6
SANTO_DOMINGO_TZ = ZoneInfo("America/Santo_Domingo")


def _report_created_at_sd(report: models.Report) -> str:
    created_at = report.created_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(SANTO_DOMINGO_TZ)
    return f"{created_at.strftime('%d/%m/%Y %I:%M:%S %p')} Santo Domingo"


def _safe_report_path(report_path: str) -> Path:
    settings = get_settings()
    reports_dir = settings.reports_dir.resolve()
    path = Path(report_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    resolved = path.resolve()
    if reports_dir != resolved and reports_dir not in resolved.parents:
        raise HTTPException(status_code=400, detail="Ruta de reporte no permitida")
    return resolved


@router.get("/reportes", response_class=HTMLResponse)
def reports_page(
    request: Request,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    total_reports = db.scalar(select(func.count(models.Report.id))) or 0
    pages = max(1, (total_reports + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(page, pages)
    reports = db.scalars(
        select(models.Report)
        .order_by(models.Report.created_at.desc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
    ).all()
    iocs = db.scalars(select(models.IOC).order_by(models.IOC.created_at.desc()).limit(50)).all()
    report_items = [
        {
            "report": report,
            "filename": Path(report.report_path).name,
            "created_at": _report_created_at_sd(report),
        }
        for report in reports
    ]
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="reports.html",
        context={
            "active_page": "reportes",
            "report_items": report_items,
            "iocs": iocs,
            "pagination": {
                "page": page,
                "pages": pages,
                "total": total_reports,
                "page_size": PAGE_SIZE,
            },
            "filters": {},
        },
    )


@router.post("/reportes/ioc/{ioc_id}/{fmt}")
def create_report(ioc_id: int, fmt: str, db: Session = Depends(get_db)) -> RedirectResponse:
    if fmt not in {"html", "json", "csv", "pdf"}:
        raise HTTPException(status_code=400, detail="Formato no soportado")
    try:
        generate_ioc_report(db, ioc_id, fmt)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RedirectResponse(url="/reportes", status_code=303)


@router.get("/reportes/descargar/{report_id}")
def download_report(report_id: int, db: Session = Depends(get_db)) -> FileResponse:
    report = db.get(models.Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    path = _safe_report_path(report.report_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(path)


@router.post("/reportes/eliminar/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)) -> RedirectResponse:
    report = db.get(models.Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    path = _safe_report_path(report.report_path)
    if path.exists():
        path.unlink()
    db.delete(report)
    db.commit()
    return RedirectResponse(url="/reportes", status_code=303)
