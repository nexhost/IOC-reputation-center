import csv
import html
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session, selectinload

from app import models
from app.config import get_settings


REPORT_CREDITS = "Proyecto grupal | Kendry Rosario | Efre Rodríguez | Alejandro Paniagua | GESTIÓN DE PROYECTOS DE SEGURIDAD"
SANTO_DOMINGO_TZ = ZoneInfo("America/Santo_Domingo")


def santo_domingo_now() -> datetime:
    return datetime.now(SANTO_DOMINGO_TZ)


def _serialize_ioc(ioc: models.IOC) -> dict:
    created_at = ioc.created_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(SANTO_DOMINGO_TZ)
    return {
        "ioc": ioc.ioc_value,
        "tipo": ioc.ioc_type,
        "score_final": ioc.risk_score,
        "nivel_riesgo": ioc.verdict,
        "fecha": created_at.strftime("%d/%m/%Y %I:%M:%S %p"),
        "resultados": [
            {
                "fuente": result.source,
                "resultado": result.result,
                "score": result.score,
                "evidencia": result.raw_json,
            }
            for result in ioc.results
        ],
        "recomendaciones": recommendations_for_score(ioc.risk_score),
    }


def recommendations_for_score(score: int) -> list[str]:
    if score >= 81:
        return ["Bloquear inmediatamente", "Abrir caso critico", "Correlacionar con SIEM/EDR"]
    if score >= 61:
        return ["Bloquear preventivamente", "Validar alcance interno", "Monitorear recurrencia"]
    if score >= 41:
        return ["Mantener bajo observacion", "Revisar evidencias por fuente"]
    if score >= 21:
        return ["Correlacionar con eventos recientes", "Reconsultar si hay nueva actividad"]
    return ["Sin accion inmediata", "Mantener registro historico"]


def _risk_color(score: int) -> str:
    if score >= 81:
        return "#ef4444"
    if score >= 61:
        return "#f97316"
    if score >= 41:
        return "#eab308"
    if score >= 21:
        return "#38bdf8"
    return "#22c55e"


def _build_professional_report_html(data: dict) -> str:
    safe_ioc = html.escape(str(data["ioc"]))
    safe_type = html.escape(str(data["tipo"]))
    safe_verdict = html.escape(str(data["nivel_riesgo"]))
    risk_color = _risk_color(int(data["score_final"]))
    source_rows = []
    source_bars = []
    for result in data["resultados"]:
        source = html.escape(str(result["fuente"]))
        verdict = html.escape(str(result["resultado"]))
        score = int(result["score"])
        source_rows.append(
            f"<tr><td>{source}</td><td>{verdict}</td><td><strong>{score}/100</strong></td></tr>"
        )
        source_bars.append(
            f"""<div class="bar-row"><span>{source}</span><div><b style="width:{score}%"></b></div><strong>{score}</strong></div>"""
        )

    recommendations = "".join(f"<li>{html.escape(item)}</li>" for item in data["recomendaciones"])
    source_rows_html = "".join(source_rows) or "<tr><td colspan='3'>Sin resultados por fuente</td></tr>"
    source_bars_html = "".join(source_bars) or "<p>Sin datos para graficar.</p>"
    generated_at = f"{santo_domingo_now().strftime('%d/%m/%Y %I:%M:%S %p')} Santo Domingo"

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Reporte IOC - {safe_ioc}</title>
<style>
@page {{ size: A4; margin: 18mm; }}
* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    background: #eef3f8;
    color: #132033;
    font-family: Arial, Helvetica, sans-serif;
}}
.report {{
    max-width: 1060px;
    margin: 0 auto;
    background: #ffffff;
    border: 1px solid #d7e0ea;
}}
.hero {{
    padding: 30px;
    color: #fff;
    background: linear-gradient(135deg, #071320, #102a43 58%, #123d73);
}}
.brand {{ display: flex; gap: 14px; align-items: center; }}
.shield {{
    width: 52px; height: 52px; border: 2px solid #60a5fa; border-radius: 14px;
    display: grid; place-items: center; font-weight: 800; color: #93c5fd;
}}
.brand h1 {{ margin: 0; font-size: 24px; letter-spacing: .4px; }}
.brand p {{ margin: 5px 0 0; color: #cbd5e1; }}
.summary {{
    display: grid; grid-template-columns: 1.1fr .9fr .9fr; gap: 16px;
    margin-top: 28px;
}}
.summary-card {{
    background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.16);
    border-radius: 10px; padding: 16px;
}}
.summary-card span {{ display: block; color: #cbd5e1; font-size: 12px; }}
.summary-card strong {{ display: block; margin-top: 8px; font-size: 20px; overflow-wrap: anywhere; }}
.content {{ padding: 28px 30px 34px; }}
.grid {{ display: grid; grid-template-columns: 300px 1fr; gap: 22px; }}
.score-box {{
    border: 1px solid #d7e0ea; border-radius: 12px; padding: 20px; text-align: center;
}}
.score-ring {{
    width: 178px; height: 178px; border-radius: 50%; margin: 0 auto 14px;
    display: grid; place-items: center;
    background: radial-gradient(circle, #fff 54%, transparent 56%), conic-gradient({risk_color} {int(data["score_final"])}%, #e5e7eb 0);
}}
.score-ring strong {{ color: {risk_color}; font-size: 42px; }}
h2 {{ margin: 0 0 14px; font-size: 16px; color: #0f172a; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{ padding: 11px 12px; border-bottom: 1px solid #e5edf5; text-align: left; }}
th {{ color: #475569; background: #f8fafc; }}
.bar-row {{ display: grid; grid-template-columns: 130px 1fr 44px; gap: 10px; align-items: center; margin: 10px 0; font-size: 13px; }}
.bar-row div {{ height: 12px; border-radius: 999px; background: #e5e7eb; overflow: hidden; }}
.bar-row b {{ display: block; height: 100%; background: linear-gradient(90deg, #2563eb, {risk_color}); }}
.section {{ margin-top: 24px; border: 1px solid #d7e0ea; border-radius: 12px; padding: 18px; }}
ul {{ margin: 0; padding-left: 20px; }}
li {{ margin: 8px 0; }}
.footer {{ padding: 16px 30px; color: #64748b; font-size: 12px; border-top: 1px solid #e5edf5; }}
@media print {{ body {{ background: #fff; }} .report {{ border: 0; }} }}
</style>
</head>
<body>
<main class="report">
    <section class="hero">
        <div class="brand">
            <div class="shield">IOC</div>
            <div>
                <h1>IOC REPUTATION CENTER</h1>
                <p>Threat Intelligence &amp; Analysis</p>
            </div>
        </div>
        <div class="summary">
            <div class="summary-card"><span>Indicador consultado</span><strong>{safe_ioc}</strong></div>
            <div class="summary-card"><span>Tipo de IOC</span><strong>{safe_type}</strong></div>
            <div class="summary-card"><span>Generado</span><strong>{generated_at}</strong></div>
        </div>
    </section>
    <section class="content">
        <div class="grid">
            <div class="score-box">
                <div class="score-ring"><strong>{int(data["score_final"])}</strong></div>
                <h2>Nivel de riesgo</h2>
                <p><strong style="color:{risk_color}">{safe_verdict}</strong></p>
            </div>
            <div class="section" style="margin-top:0">
                <h2>Resultados por fuente</h2>
                {source_bars_html}
            </div>
        </div>
        <div class="section">
            <h2>Detalle de fuentes</h2>
            <table><thead><tr><th>Fuente</th><th>Resultado</th><th>Score</th></tr></thead><tbody>{source_rows_html}</tbody></table>
        </div>
        <div class="section">
            <h2>Recomendaciones</h2>
            <ul>{recommendations}</ul>
        </div>
    </section>
    <footer class="footer">{REPORT_CREDITS}</footer>
</main>
</body>
</html>"""


def _build_pdf_with_reportlab(data: dict, path: Path) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    header_title = ParagraphStyle("HeaderTitle", parent=styles["Title"], textColor=colors.white, fontSize=18)
    header_text = ParagraphStyle("HeaderText", parent=styles["Normal"], textColor=colors.HexColor("#dbeafe"), fontSize=10)
    document = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    story = []
    risk_color = colors.HexColor(_risk_color(int(data["score_final"])))

    header = Table(
        [[
            Paragraph("<b>IOC</b>", header_title),
            Paragraph(
                "<b>IOC REPUTATION CENTER</b><br/>Threat Intelligence &amp; Analysis",
                header_text,
            ),
            Paragraph(f"Santo Domingo<br/>{santo_domingo_now().strftime('%d/%m/%Y %I:%M:%S %p')}", header_text),
        ]],
        colWidths=[28 * mm, 92 * mm, 44 * mm],
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#071320")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#2563eb")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, 10))

    summary = Table(
        [
            ["IOC", str(data["ioc"])],
            ["Tipo", str(data["tipo"])],
            ["Nivel de riesgo", str(data["nivel_riesgo"])],
            ["Score final", f"{data['score_final']}/100"],
            ["Fecha", str(data["fecha"])],
        ],
        colWidths=[42 * mm, 122 * mm],
    )
    summary.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#102a43")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7e0ea")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(summary)
    story.append(Spacer(1, 14))

    score_width = max(4, int(data["score_final"]) * 1.55)
    score_table = Table(
        [["Score", "", f"{data['score_final']}/100"]],
        colWidths=[25 * mm, score_width * mm / 2, 25 * mm],
    )
    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
                ("BACKGROUND", (1, 0), (1, 0), risk_color),
                ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7e0ea")),
            ]
        )
    )
    story.append(Paragraph("<b>Grafico de riesgo</b>", styles["Heading2"]))
    story.append(score_table)
    story.append(Spacer(1, 14))

    rows = [["Fuente", "Resultado", "Score"]]
    for result in data["resultados"]:
        rows.append([str(result["fuente"]), str(result["resultado"]), f"{result['score']}/100"])
    results_table = Table(rows, colWidths=[58 * mm, 68 * mm, 34 * mm])
    results_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#102a43")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7e0ea")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ffffff")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.append(Paragraph("<b>Detalle por fuente</b>", styles["Heading2"]))
    story.append(results_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("<b>Recomendaciones</b>", styles["Heading2"]))
    for item in data["recomendaciones"]:
        story.append(Paragraph(f"- {html.escape(item)}", styles["Normal"]))

    story.append(Spacer(1, 14))
    story.append(Paragraph(REPORT_CREDITS, styles["Normal"]))
    document.build(story)


def generate_ioc_report(db: Session, ioc_id: int, fmt: str) -> Path:
    settings = get_settings()
    settings.reports_dir.mkdir(exist_ok=True)
    ioc = db.get(
        models.IOC,
        ioc_id,
        options=[selectinload(models.IOC.results)],
    )
    if ioc is None:
        raise ValueError("IOC no encontrado")

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_name = f"ioc_{ioc.id}_{timestamp}"
    data = _serialize_ioc(ioc)

    if fmt == "json":
        path = settings.reports_dir / f"{safe_name}.json"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    elif fmt == "csv":
        path = settings.reports_dir / f"{safe_name}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["IOC", "Tipo", "Fuente", "Resultado", "Score", "Score Final", "Riesgo"])
            for result in data["resultados"]:
                writer.writerow(
                    [
                        data["ioc"],
                        data["tipo"],
                        result["fuente"],
                        result["resultado"],
                        result["score"],
                        data["score_final"],
                        data["nivel_riesgo"],
                    ]
                )
    elif fmt in {"html", "pdf"}:
        path = settings.reports_dir / f"{safe_name}.html"
        report_html = _build_professional_report_html(data)
        if fmt == "pdf":
            path = settings.reports_dir / f"{safe_name}.pdf"
            _build_pdf_with_reportlab(data, path)
        else:
            path.write_text(report_html, encoding="utf-8")
    else:
        raise ValueError("Formato no soportado")

    report = models.Report(report_path=str(path))
    db.add(report)
    db.commit()
    return path
