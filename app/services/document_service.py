from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


DOCS_DIR = Path("docs")

DOCUMENTS = {
    "manual-uso": {
        "title": "Manual de uso",
        "filename": "manual-uso-ioc-reputation-center.pdf",
        "sections": [
            "Acceda al sistema desde http://127.0.0.1:8000 e inicie sesion con una cuenta autorizada.",
            "Use Consulta IOC para verificar IP, dominio, URL o hash contra fuentes de inteligencia.",
            "Revise Dashboard, Alertas, Historial y Casos para seguimiento operativo.",
        ],
    },
    "politica-privacidad": {
        "title": "Politica de privacidad",
        "filename": "politica-privacidad-ioc-reputation-center.pdf",
        "sections": [
            "Las API keys deben guardarse en la configuracion local y no subirse al repositorio.",
            "La herramienta es defensiva y registra consultas para auditoria interna.",
            "No debe almacenarse informacion personal innecesaria ni contrasenas en texto claro.",
        ],
    },
    "proceso-consulta": {
        "title": "Proceso de consulta IOC",
        "filename": "proceso-consulta-ioc-reputation-center.pdf",
        "sections": [
            "Identifique el indicador y valide su formato antes de consultar.",
            "Revise resultados por fuente, score final, recomendacion y evidencia.",
            "Si el score es alto o malicioso, cree un caso y documente la linea de tiempo.",
        ],
    },
    "guia-linux": {
        "title": "Guia de instalacion y uso en Linux",
        "filename": "guia-linux-ioc-reputation-center.pdf",
        "sections": [
            "Instale Python 3.11+, git y python3-venv en Kali Linux o Ubuntu.",
            "Cree el entorno virtual con python3 -m venv venv y ejecute pip install -r requirements.txt.",
            "Levante el servicio con uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload.",
        ],
    },
}


def generate_document(slug: str) -> Path:
    if slug not in DOCUMENTS:
        raise ValueError("Documento no encontrado")
    DOCS_DIR.mkdir(exist_ok=True)
    data = DOCUMENTS[slug]
    path = DOCS_DIR / data["filename"]
    if path.exists():
        return path

    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm)
    story = []
    header = Table([["IOC", "IOC REPUTATION CENTER\nThreat Intelligence & Analysis"]], colWidths=[28 * mm, 136 * mm])
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#071320")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#2563eb")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, 16))
    story.append(Paragraph(f"<b>{data['title']}</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    for section in data["sections"]:
        story.append(Paragraph(f"- {section}", styles["Normal"]))
        story.append(Spacer(1, 8))
    story.append(Spacer(1, 18))
    story.append(Paragraph("Proyecto grupal | Kendry Rosario | Efre Rodriguez | Alejandro Paniagua | GESTION DE PROYECTOS DE SEGURIDAD", styles["Normal"]))
    document.build(story)
    return path
