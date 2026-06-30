from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.config import get_settings


SOURCE_DEFINITIONS = [
    {
        "source": "ThreatFox",
        "display_name": "ThreatFox",
        "api_url": "https://threatfox-api.abuse.ch/api/v1/",
        "notes": "IOC malware, botnets y amenazas de abuse.ch.",
    },
    {
        "source": "URLHaus",
        "display_name": "URLHaus",
        "api_url": "https://urlhaus-api.abuse.ch/v1/",
        "notes": "URLs y hosts asociados a malware.",
    },
    {
        "source": "AbuseIPDB",
        "display_name": "AbuseIPDB",
        "api_url": "https://api.abuseipdb.com/api/v2/check",
        "notes": "Reputacion de direcciones IP reportadas por abuso.",
    },
    {
        "source": "VirusTotal",
        "display_name": "VirusTotal",
        "api_url": "https://www.virustotal.com/api/v3/",
        "notes": "Reputacion multi-engine para IP, dominio, URL y hashes.",
    },
    {
        "source": "AlienVault OTX",
        "display_name": "AlienVault OTX",
        "api_url": "https://otx.alienvault.com/api/v1/",
        "notes": "Pulses y contexto de amenaza de AlienVault OTX.",
    },
    {
        "source": "Have I Been Pwned",
        "display_name": "Have I Been Pwned",
        "api_url": "https://haveibeenpwned.com/api/v3/",
        "notes": "Brechas historicas asociadas a cuentas de correo.",
    },
]


def seed_source_configs(db: Session) -> None:
    settings = get_settings()
    defaults = {
        "ThreatFox": {"api_url": settings.threatfox_api_url, "api_key": ""},
        "URLHaus": {"api_url": settings.urlhaus_api_url, "api_key": ""},
        "AbuseIPDB": {"api_url": "https://api.abuseipdb.com/api/v2/check", "api_key": settings.abuseipdb_api_key or ""},
        "VirusTotal": {"api_url": "https://www.virustotal.com/api/v3/", "api_key": settings.virustotal_api_key or ""},
        "AlienVault OTX": {"api_url": "https://otx.alienvault.com/api/v1/", "api_key": settings.otx_api_key or ""},
        "Have I Been Pwned": {"api_url": "https://haveibeenpwned.com/api/v3/", "api_key": settings.hibp_api_key or ""},
    }
    for definition in SOURCE_DEFINITIONS:
        existing = db.scalar(select(models.SourceConfig).where(models.SourceConfig.source == definition["source"]))
        if existing:
            continue
        db.add(
            models.SourceConfig(
                source=definition["source"],
                display_name=definition["display_name"],
                api_url=defaults[definition["source"]]["api_url"] or definition["api_url"],
                api_key=defaults[definition["source"]]["api_key"],
                is_enabled=True,
                notes=definition["notes"],
            )
        )
    db.commit()


def list_source_configs(db: Session) -> list[models.SourceConfig]:
    seed_source_configs(db)
    return db.scalars(select(models.SourceConfig).order_by(models.SourceConfig.display_name)).all()


def get_source_config(db: Session | None, source: str) -> models.SourceConfig | None:
    if db is None:
        return None
    seed_source_configs(db)
    return db.scalar(select(models.SourceConfig).where(models.SourceConfig.source == source))


def update_source_config(
    db: Session,
    source: str,
    api_url: str,
    api_key: str,
    is_enabled: bool,
) -> models.SourceConfig:
    config = db.scalar(select(models.SourceConfig).where(models.SourceConfig.source == source))
    if config is None:
        raise ValueError("Fuente no encontrada.")
    config.api_url = api_url.strip()
    if api_key.strip() and api_key.strip() != "__keep__":
        config.api_key = api_key.strip()
    config.is_enabled = is_enabled
    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    return config


def mask_key(value: str | None) -> str:
    if not value:
        return "Pendiente"
    if len(value) <= 8:
        return "Configurada"
    return f"{value[:4]}...{value[-4:]}"
