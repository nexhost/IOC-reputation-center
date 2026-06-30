import requests
from sqlalchemy.orm import Session

from app.config import get_settings
from app.schemas import SourceResult
from app.services.source_config_service import get_source_config


class ThreatFoxService:
    name = "ThreatFox"

    def __init__(self, db: Session | None = None) -> None:
        self.settings = get_settings()
        self.config = get_source_config(db, self.name)

    def lookup(self, value: str, ioc_type: str) -> SourceResult:
        payload = {"query": "search_ioc", "search_term": value}
        if self.config and not self.config.is_enabled:
            return SourceResult(source=self.name, result="Deshabilitado", score=0, online=False)
        api_url = self.config.api_url if self.config and self.config.api_url else self.settings.threatfox_api_url
        try:
            response = requests.post(
                api_url,
                json=payload,
                timeout=self.settings.request_timeout,
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

        if data.get("query_status") == "ok" and data.get("data"):
            records = data["data"]
            confidence = max(int(item.get("confidence_level") or 75) for item in records)
            return SourceResult(
                source=self.name,
                result="Malicioso",
                score=min(100, max(70, confidence)),
                evidence={"matches": len(records), "sample": records[:3]},
            )

        return SourceResult(
            source=self.name,
            result="Sin hallazgos",
            score=0,
            evidence={"query_status": data.get("query_status", "unknown")},
        )
