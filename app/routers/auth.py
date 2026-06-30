from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import authenticate_user


router = APIRouter(tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = "/") -> HTMLResponse:
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=303)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"next": next, "error": None},
    )


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, email, password)
    if user is None:
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"next": next or "/", "error": "Credenciales invalidas o usuario inactivo."},
            status_code=401,
        )
    request.session["user_id"] = user.id
    return RedirectResponse(url=next or "/", status_code=303)


@router.post("/logout")
def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
