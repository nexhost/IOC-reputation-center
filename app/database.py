from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def ensure_schema() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    statements = []
    if "password_hash" not in existing_columns:
        statements.append("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) DEFAULT ''")
    if "is_active" not in existing_columns:
        statements.append("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
    if "last_login" not in existing_columns:
        statements.append("ALTER TABLE users ADD COLUMN last_login DATETIME")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

    table_names = inspector.get_table_names()
    if "source_configs" not in table_names:
        from app import models  # noqa: F401

        Base.metadata.tables["source_configs"].create(bind=engine, checkfirst=True)
    if "case_events" not in table_names:
        from app import models  # noqa: F401

        Base.metadata.tables["case_events"].create(bind=engine, checkfirst=True)
