import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.services.auth_service import ensure_admin_credentials
from app.services.source_config_service import seed_source_configs


def seed_initial_data(db: Session) -> None:
    ensure_admin_credentials(db)
    seed_source_configs(db)

    if db.scalar(select(models.IOC).limit(1)) is not None:
        db.commit()
        return

    samples = [
        ("IP", "185.220.101.45", 78, "Critico", "ThreatFox", "Malicioso"),
        ("Dominio", "malware-update.com", 56, "Alto", "URLHaus", "Sospechoso"),
        ("URL", "https://malicious.com/payload.exe", 92, "Malicioso", "URLHaus", "Malicioso"),
        ("MD5", "44d88612fea8a8f36de82e1278abb02f", 10, "Bajo", "VirusTotal", "Sin hallazgos"),
        ("IP", "8.8.8.8", 0, "Bajo", "AbuseIPDB", "Sin hallazgos"),
    ]
    for ioc_type, value, score, verdict, source, result in samples:
        ioc = models.IOC(ioc_type=ioc_type, ioc_value=value, risk_score=score, verdict=verdict)
        db.add(ioc)
        db.flush()
        db.add(
            models.ReputationResult(
                ioc_id=ioc.id,
                source=source,
                result=result,
                score=score,
                raw_json=json.dumps({"seed": True, "source": source}),
            )
        )

    case = models.Case(
        name="Caso #23 - Infraestructura TOR sospechosa",
        description="Investigacion inicial sobre IP reportada por multiples fuentes.",
        status="En investigacion",
        analyst_notes="Priorizar correlacion con logs de proxy y EDR.",
    )
    db.add(case)
    db.commit()
