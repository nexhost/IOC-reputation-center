from app.schemas import SourceResult


def classify_score(score: int) -> str:
    if score <= 20:
        return "Bajo"
    if score <= 40:
        return "Moderado"
    if score <= 60:
        return "Alto"
    if score <= 80:
        return "Critico"
    return "Malicioso"


def dashboard_bucket(verdict: str, score: int) -> str:
    if verdict in {"Malicioso", "Critico"} or score >= 61:
        return "Malicioso"
    if verdict in {"Moderado", "Alto"} or 21 <= score <= 60:
        return "Sospechoso"
    return "Limpio"


def calculate_final_score(results: list[SourceResult]) -> int:
    scored = [result.score for result in results if result.online or result.score > 0]
    if not scored:
        return 0

    max_score = max(scored)
    average_score = sum(scored) / len(scored)
    positive_sources = sum(1 for result in results if result.score >= 60)
    confidence_bonus = min(12, positive_sources * 4)
    final_score = round((max_score * 0.65) + (average_score * 0.35) + confidence_bonus)
    return max(0, min(100, final_score))
