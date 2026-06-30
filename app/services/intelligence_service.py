from sqlalchemy.orm import Session

from app.schemas import SourceResult
from app.services.abuseipdb_service import AbuseIPDBService
from app.services.threatfox_service import ThreatFoxService
from app.services.urlhaus_service import URLHausService
from app.services.virustotal_service import VirusTotalService

IOC_LOOKUP_SOURCES = ("ThreatFox", "URLHaus", "AbuseIPDB", "VirusTotal")


class IntelligenceService:
    def __init__(self, db: Session | None = None) -> None:
        self.services = [
            ThreatFoxService(db),
            URLHausService(db),
            AbuseIPDBService(db),
            VirusTotalService(db),
        ]

    def lookup_all(self, value: str, ioc_type: str) -> list[SourceResult]:
        return [service.lookup(value, ioc_type) for service in self.services]
