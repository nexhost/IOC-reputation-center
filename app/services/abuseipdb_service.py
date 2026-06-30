import requests
from sqlalchemy.orm import Session

from app.config import get_settings
from app.schemas import SourceResult
from app.services.source_config_service import get_source_config


class AbuseIPDBService:
    name = "AbuseIPDB"

    def __init__(self, db: Session | None = None) -> None:
        self.settings = get_settings()
        self.config = get_source_config(db, self.name)

    def lookup(self, value: str, ioc_type: str) -> SourceResult:
        if ioc_type != "IP":
            return SourceResult(
                source=self.name,
                result="No aplica",
                score=0,
                evidence={"reason": "AbuseIPDB solo consulta IPs."},
            )
        if self.config and not self.config.is_enabled:
            return SourceResult(source=self.name, result="Deshabilitado", score=0, online=False)
        api_key = self.config.api_key if self.config and self.config.api_key else self.settings.abuseipdb_api_key
        api_url = self.config.api_url if self.config and self.config.api_url else "https://api.abuseipdb.com/api/v2/check"
        if not api_key:
            return SourceResult(
                source=self.name,
                result="Sin API key",
                score=0,
                online=False,
                evidence={"env": "ABUSEIPDB_API_KEY"},
            )

        try:
            response = requests.get(
                api_url,
                headers={
                    "Key": api_key,
                    "Accept": "application/json",
                },
                params={"ipAddress": value, "maxAgeInDays": 90, "verbose": ""},
                timeout=self.settings.request_timeout,
            )
            response.raise_for_status()
            data = response.json().get("data", {})
        except requests.RequestException as exc:
            return SourceResult(
                source=self.name,
                result="Error",
                score=0,
                online=False,
                evidence={"error": str(exc)},
            )

        score = int(data.get("abuseConfidenceScore") or 0)
        result = "Malicioso" if score >= 70 else "Sospechoso" if score >= 25 else "Sin hallazgos"
        return SourceResult(source=self.name, result=result, score=score, evidence=data)
