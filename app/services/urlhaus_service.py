import requests
from sqlalchemy.orm import Session

from app.config import get_settings
from app.schemas import SourceResult
from app.services.source_config_service import get_source_config


class URLHausService:
    name = "URLHaus"

    def __init__(self, db: Session | None = None) -> None:
        self.settings = get_settings()
        self.config = get_source_config(db, self.name)

    def lookup(self, value: str, ioc_type: str) -> SourceResult:
        if ioc_type not in {"URL", "Dominio"}:
            return SourceResult(
                source=self.name,
                result="No aplica",
                score=0,
                evidence={"reason": "URLHaus consulta URLs y hosts."},
            )
        if self.config and not self.config.is_enabled:
            return SourceResult(source=self.name, result="Deshabilitado", score=0, online=False)

        endpoint = "url/" if ioc_type == "URL" else "host/"
        field = "url" if ioc_type == "URL" else "host"
        api_url = self.config.api_url if self.config and self.config.api_url else self.settings.urlhaus_api_url
        try:
            response = requests.post(
                f"{api_url.rstrip('/')}/{endpoint}",
                data={field: value},
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

        if data.get("query_status") == "ok":
            status = data.get("url_status") or data.get("host_status") or "listed"
            score = 92 if status == "online" else 70
            return SourceResult(
                source=self.name,
                result="Malicioso",
                score=score,
                evidence=data,
            )

        return SourceResult(
            source=self.name,
            result="Sin hallazgos",
            score=0,
            evidence={"query_status": data.get("query_status", "unknown")},
        )
