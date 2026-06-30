import json

from sqlalchemy.orm import Session

from app import models
from app.schemas import IOCResponse, SourceResult
from app.services.audit_service import audit
from app.services.intelligence_service import IntelligenceService
from app.services.ioc_utils import detect_ioc_type, normalize_ioc
from app.services.risk_engine import calculate_final_score, classify_score


def query_ioc(db: Session, value: str, analyst: str = "Analista SOC") -> IOCResponse:
    normalized = normalize_ioc(value)
    ioc_type = detect_ioc_type(normalized)
    source_results = IntelligenceService(db).lookup_all(normalized, ioc_type)
    risk_score = calculate_final_score(source_results)
    verdict = classify_score(risk_score)

    ioc = models.IOC(
        ioc_type=ioc_type,
        ioc_value=normalized,
        risk_score=risk_score,
        verdict=verdict,
    )
    db.add(ioc)
    db.flush()

    for result in source_results:
        db.add(
            models.ReputationResult(
                ioc_id=ioc.id,
                source=result.source,
                result=result.result,
                score=result.score,
                raw_json=json.dumps(result.evidence, ensure_ascii=False, default=str),
            )
        )

    db.commit()
    db.refresh(ioc)
    audit("ioc_lookup", ioc=normalized, ioc_type=ioc_type, score=risk_score, analyst=analyst)
    return IOCResponse(
        id=ioc.id,
        ioc_type=ioc.ioc_type,
        ioc_value=ioc.ioc_value,
        verdict=ioc.verdict,
        risk_score=ioc.risk_score,
        source_results=source_results,
        created_at=ioc.created_at,
    )


def result_to_schema(result: models.ReputationResult) -> SourceResult:
    try:
        evidence = json.loads(result.raw_json or "{}")
    except json.JSONDecodeError:
        evidence = {"raw": result.raw_json}
    return SourceResult(
        source=result.source,
        result=result.result,
        score=result.score,
        evidence=evidence,
        online=result.result not in {"Error", "Sin API key"},
    )
