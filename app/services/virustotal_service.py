import hashlib
import requests
from sqlalchemy.orm import Session

from app.config import get_settings
from app.schemas import SourceResult
from app.services.source_config_service import get_source_config


class VirusTotalService:
    name = "VirusTotal"

    def __init__(self, db: Session | None = None) -> None:
        self.settings = get_settings()
        self.config = get_source_config(db, self.name)

    def lookup(self, value: str, ioc_type: str) -> SourceResult:
        if self.config and not self.config.is_enabled:
            return SourceResult(source=self.name, result="Deshabilitado", score=0, online=False)
        api_key = self.config.api_key if self.config and self.config.api_key else self.settings.virustotal_api_key
        api_url = self.config.api_url if self.config and self.config.api_url else "https://www.virustotal.com/api/v3/"
        if not api_key:
            return SourceResult(
                source=self.name,
                result="Sin API key",
                score=0,
                online=False,
                evidence={"env": "VIRUSTOTAL_API_KEY"},
            )

        vt_type = self._vt_type(ioc_type)
        vt_value = hashlib.sha256(value.encode()).hexdigest() if ioc_type == "URL" else value
        try:
            response = requests.get(
                f"{api_url.rstrip('/')}/{vt_type}/{vt_value}",
                headers={"x-apikey": api_key},
                timeout=self.settings.request_timeout,
            )
            if response.status_code == 404:
                return SourceResult(
                    source=self.name,
                    result="Sin hallazgos",
                    score=0,
                    evidence={"status_code": 404},
                )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            return SourceResult(
                source=self.name,
                result="Error",
                score=0,
                online=False,
                evidence={"error": str(exc)},
            )

        stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        malicious = int(stats.get("malicious") or 0)
        suspicious = int(stats.get("suspicious") or 0)
        total = max(1, sum(int(value or 0) for value in stats.values()))
        score = min(100, round(((malicious * 1.0) + (suspicious * 0.45)) / total * 100))
        result = "Malicioso" if malicious else "Sospechoso" if suspicious else "Sin hallazgos"
        return SourceResult(source=self.name, result=result, score=score, evidence=data)

    @staticmethod
    def _vt_type(ioc_type: str) -> str:
        mapping = {
            "IP": "ip_addresses",
            "Dominio": "domains",
            "URL": "urls",
            "MD5": "files",
            "SHA1": "files",
            "SHA256": "files",
        }
        return mapping[ioc_type]
