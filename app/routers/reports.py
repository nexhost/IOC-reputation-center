from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.services.report_service import generate_ioc_report


router = APIRouter(tags=["reports"])


@router.get("/reportes", response_class=HTMLResponse)
def reports_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    reports = db.scalars(select(models.Report).order_by(models.Report.created_at.desc())).all()
    iocs = db.scalars(select(models.IOC).order_by(models.IOC.created_at.desc()).limit(50)).all()
    report_items = [{"report": report, "filename": Path(report.report_path).name} for report in reports]
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="reports.html",
        context={"active_page": "reportes", "report_items": report_items, "iocs": iocs},
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
    path = Path(report.report_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(path)
