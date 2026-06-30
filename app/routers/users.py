from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.services.auth_service import ROLES, create_user, hash_password


router = APIRouter(tags=["users"])


def require_admin(request: Request) -> None:
    user = getattr(request.state, "user", None)
    if user is None or user.role != "Administrador":
        raise HTTPException(status_code=403, detail="Permiso requerido: Administrador")


@router.get("/usuarios", response_class=HTMLResponse)
def users_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    users = db.scalars(select(models.User).order_by(models.User.created_at.desc())).all()
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="users.html",
        context={"active_page": "usuarios", "users": users, "roles": ROLES, "error": None},
    )


@router.post("/usuarios", response_class=HTMLResponse)
def create_user_page(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    password: str = Form(...),
    is_active: str | None = Form(None),
    db: Session = Depends(get_db),
):
    require_admin(request)
    try:
        create_user(db, name=name, email=email, role=role, password=password, is_active=is_active == "on")
    except ValueError as exc:
        users = db.scalars(select(models.User).order_by(models.User.created_at.desc())).all()
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="users.html",
            context={"active_page": "usuarios", "users": users, "roles": ROLES, "error": str(exc)},
            status_code=400,
        )
    return RedirectResponse(url="/usuarios", status_code=303)


@router.post("/usuarios/{user_id}/estado")
def toggle_user_status(user_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    require_admin(request)
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    current_user = getattr(request.state, "user", None)
    if current_user and current_user.id == user.id:
        raise HTTPException(status_code=400, detail="No puede desactivar su propia cuenta")
    user.is_active = not user.is_active
    db.commit()
    return RedirectResponse(url="/usuarios", status_code=303)


@router.post("/usuarios/{user_id}/editar")
def edit_user(
    user_id: int,
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    is_active: str | None = Form(None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    require_admin(request)
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    normalized_email = email.strip().lower()
    duplicated = db.scalar(select(models.User).where(models.User.email == normalized_email, models.User.id != user_id))
    if duplicated:
        raise HTTPException(status_code=400, detail="Ya existe otro usuario con ese correo")
    if role not in ROLES:
        raise HTTPException(status_code=400, detail="Rol no permitido")

    current_user = getattr(request.state, "user", None)
    if current_user and current_user.id == user.id and role != "Administrador":
        raise HTTPException(status_code=400, detail="No puede quitar su propio rol administrador")
    if current_user and current_user.id == user.id and is_active != "on":
        raise HTTPException(status_code=400, detail="No puede desactivar su propia cuenta")

    user.name = name.strip()
    user.email = normalized_email
    user.role = role
    user.is_active = is_active == "on"
    db.commit()
    return RedirectResponse(url="/usuarios", status_code=303)


@router.post("/usuarios/{user_id}/password")
def reset_password(
    user_id: int,
    request: Request,
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    require_admin(request)
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.password_hash = hash_password(password)
    db.commit()
    return RedirectResponse(url="/usuarios", status_code=303)
