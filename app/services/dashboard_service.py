from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app import models
from app.config import get_settings
from app.services.intelligence_service import IOC_LOOKUP_SOURCES
from app.services.risk_engine import dashboard_bucket
from app.services.source_config_service import list_source_configs


def get_source_health(db: Session) -> list[dict]:
    settings = get_settings()
    configs = {config.source: config for config in list_source_configs(db)}
    env_keys = {
        "AbuseIPDB": settings.abuseipdb_api_key,
        "VirusTotal": settings.virustotal_api_key,
    }
    source_health = []
    for source in IOC_LOOKUP_SOURCES:
        config = configs.get(source)
        enabled = config.is_enabled if config else True
        requires_key = source in env_keys
        has_key = bool((config and config.api_key) or env_keys.get(source))
        online = enabled and (not requires_key or has_key)
        source_health.append(
            {
                "name": source,
                "online": online,
                "requires_key": requires_key,
                "has_key": has_key,
            }
        )
    return source_health


def get_dashboard_context(db: Session) -> dict:
    iocs = db.scalars(
        select(models.IOC).options(selectinload(models.IOC.results)).order_by(models.IOC.created_at.desc())
    ).all()
    cases_active = db.scalar(
        select(func.count(models.Case.id)).where(models.Case.status.in_(["Abierto", "En investigacion"]))
    ) or 0

    buckets = Counter(dashboard_bucket(ioc.verdict, ioc.risk_score) for ioc in iocs)
    type_counts = Counter(ioc.ioc_type for ioc in iocs)
    severity_counts = {
        "Critico": sum(1 for ioc in iocs if 61 <= ioc.risk_score <= 80),
        "Alto": sum(1 for ioc in iocs if 41 <= ioc.risk_score <= 60),
        "Medio": sum(1 for ioc in iocs if 21 <= ioc.risk_score <= 40),
        "Bajo": sum(1 for ioc in iocs if 1 <= ioc.risk_score <= 20),
        "Informacional": sum(1 for ioc in iocs if ioc.risk_score == 0),
    }
    last_ioc = iocs[0] if iocs else None

    return {
        "total_iocs": len(iocs),
        "malicious_iocs": buckets["Malicioso"],
        "suspicious_iocs": buckets["Sospechoso"],
        "clean_iocs": buckets["Limpio"],
        "active_cases": cases_active,
        "last_ioc": last_ioc,
        "latest_iocs": iocs[:8],
        "source_health": get_source_health(db),
        "type_counts": {
            "IP": type_counts["IP"],
            "Dominio": type_counts["Dominio"],
            "URL": type_counts["URL"],
            "Hash SHA256": type_counts["SHA256"] + type_counts["SHA1"],
            "Hash MD5": type_counts["MD5"],
        },
        "severity_counts": severity_counts,
        "top_countries": [
            {"name": "Rusia", "value": 28.5, "color": "#ef4444"},
            {"name": "Estados Unidos", "value": 18.7, "color": "#f97316"},
            {"name": "China", "value": 12.9, "color": "#eab308"},
            {"name": "Paises Bajos", "value": 7.3, "color": "#86efac"},
            {"name": "Alemania", "value": 5.8, "color": "#5eead4"},
            {"name": "Otros", "value": 26.8, "color": "#cbd5e1"},
        ],
        "activities": [
            {"title": "Nueva consulta de IOC realizada", "detail": last_ioc.ioc_value if last_ioc else "-", "time": "Hace 2 min"},
            {"title": "Caso #23 actualizado", "detail": "Analisis completado", "time": "Hace 10 min"},
            {"title": "Reporte generado", "detail": "Reporte_Semanal.pdf", "time": "Hace 30 min"},
            {"title": "Nuevo usuario registrado", "detail": "analista2@soc.local", "time": "Hace 1 hora"},
        ],
    }
