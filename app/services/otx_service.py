from urllib.parse import quote

import requests
from sqlalchemy.orm import Session

from app.config import get_settings
from app.schemas import SourceResult
from app.services.source_config_service import get_source_config


class OTXService:
    name = "AlienVault OTX"

    def __init__(self, db: Session | None = None) -> None:
        self.settings = get_settings()
        self.config = get_source_config(db, self.name)

    def lookup(self, value: str, ioc_type: str) -> SourceResult:
        if self.config and not self.config.is_enabled:
            return SourceResult(source=self.name, result="Deshabilitado", score=0, online=False)

        api_key = self.config.api_key if self.config and self.config.api_key else self.settings.otx_api_key
        api_url = self.config.api_url if self.config and self.config.api_url else "https://otx.alienvault.com/api/v1/"
        if not api_key:
            return SourceResult(
                source=self.name,
                result="Sin API key",
                score=0,
                online=False,
                evidence={"env": "OTX_API_KEY"},
            )

        indicator_type = self._indicator_type(ioc_type)
        if not indicator_type:
            return SourceResult(
                source=self.name,
                result="No aplica",
                score=0,
                evidence={"reason": "Tipo de IOC no soportado por OTX."},
            )

        try:
            response = requests.get(
                f"{api_url.rstrip('/')}/indicators/{indicator_type}/{quote(value, safe='')}/general",
                headers={"X-OTX-API-KEY": api_key},
                timeout=self.settings.request_timeout,
            )
            if response.status_code == 404:
                return SourceResult(source=self.name, result="Sin hallazgos", score=0, evidence={"status_code": 404})
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

        pulse_count = int(data.get("pulse_info", {}).get("count") or 0)
        score = min(100, 35 + pulse_count * 10) if pulse_count else 0
        result = "Malicioso" if score >= 70 else "Sospechoso" if score > 0 else "Sin hallazgos"
        return SourceResult(source=self.name, result=result, score=score, evidence=data)

    @staticmethod
    def _indicator_type(ioc_type: str) -> str | None:
        mapping = {
            "IP": "IPv4",
            "Dominio": "domain",
            "URL": "url",
            "MD5": "file",
            "SHA1": "file",
            "SHA256": "file",
        }
        return mapping.get(ioc_type)
