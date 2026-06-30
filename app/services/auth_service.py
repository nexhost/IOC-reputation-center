import hashlib
import hmac
import secrets
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.services.audit_service import audit


DEFAULT_ADMIN_EMAIL = "analista@soc.local"
DEFAULT_ADMIN_PASSWORD = "admin123"
ROLES = ["Administrador", "Supervisor SOC", "Analista SOC", "Solo lectura"]


def hash_password(password: str) -> str:
    iterations = 240_000
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt, digest = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        test_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            int(iterations_text),
        ).hex()
        return hmac.compare_digest(test_digest, digest)
    except (ValueError, TypeError):
        return False


def authenticate_user(db: Session, email: str, password: str) -> models.User | None:
    user = db.scalar(select(models.User).where(models.User.email == email.strip().lower()))
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login = datetime.utcnow()
    db.commit()
    audit("login_success", email=user.email, role=user.role)
    return user


def create_user(
    db: Session,
    name: str,
    email: str,
    role: str,
    password: str,
    is_active: bool = True,
) -> models.User:
    normalized_email = email.strip().lower()
    if role not in ROLES:
        raise ValueError("Rol no permitido.")
    if db.scalar(select(models.User).where(models.User.email == normalized_email)):
        raise ValueError("Ya existe un usuario con ese correo.")

    user = models.User(
        name=name.strip(),
        email=normalized_email,
        role=role,
        password_hash=hash_password(password),
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    audit("user_created", email=user.email, role=user.role)
    return user


def ensure_admin_credentials(db: Session) -> None:
    admin = db.scalar(select(models.User).where(models.User.email == DEFAULT_ADMIN_EMAIL))
    if admin is None:
        create_user(
            db,
            name="Analista SOC",
            email=DEFAULT_ADMIN_EMAIL,
            role="Administrador",
            password=DEFAULT_ADMIN_PASSWORD,
        )
        return

    changed = False
    if not admin.password_hash:
        admin.password_hash = hash_password(DEFAULT_ADMIN_PASSWORD)
        changed = True
    if not admin.is_active:
        admin.is_active = True
        changed = True
    if admin.role != "Administrador":
        admin.role = "Administrador"
        changed = True
    if changed:
        db.commit()
