from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware

from app import models
from app.config import get_settings
from app.database import SessionLocal, ensure_schema, init_db
from app.routers import auth, cases, dashboard, ioc, reports, system, tools, users
from app.services.dashboard_service import get_source_health
from app.services.seed import seed_initial_data


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Threat Intelligence & IOC Analysis Platform",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.state.templates = Jinja2Templates(directory="app/templates")

for router in (
    auth.router,
    dashboard.router,
    ioc.router,
    cases.router,
    reports.router,
    users.router,
    system.router,
    tools.router,
):
    app.router.routes.extend(router.routes)


@app.middleware("http")
async def authentication_guard(request: Request, call_next):
    public_paths = ("/login", "/static", "/health", "/docs", "/redoc", "/openapi.json")
    request.state.user = None
    request.state.source_health = None
    if request.url.path.startswith(public_paths):
        return await call_next(request)

    user_id = request.session.get("user_id")
    if not user_id:
        next_url = quote(str(request.url.path))
        return RedirectResponse(url=f"/login?next={next_url}", status_code=303)

    db = SessionLocal()
    try:
        user = db.scalar(select(models.User).where(models.User.id == user_id, models.User.is_active.is_(True)))
        if user is None:
            request.session.clear()
            return RedirectResponse(url="/login", status_code=303)
        request.state.user = user
        request.state.source_health = get_source_health(db)
        return await call_next(request)
    finally:
        db.close()


app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, same_site="lax")


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    ensure_schema()
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
