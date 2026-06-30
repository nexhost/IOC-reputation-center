from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.dashboard_service import get_dashboard_context


router = APIRouter(tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    context = get_dashboard_context(db)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"active_page": "dashboard", **context},
    )


@router.get("/api/dashboard")
def dashboard_api(db: Session = Depends(get_db)) -> dict:
    return get_dashboard_context(db)
