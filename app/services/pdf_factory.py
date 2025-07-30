from io import BytesIO
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def make_certificate(cert_type: str, child_name: str = "Иванов Иван") -> BytesIO:
    """
    cert_type: 'school' | 'family'.
    Возвращает BytesIO с PDF-файлом.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    title_map = {
        "school":  "СПРАВКА об обучении",
        "family":  "СПРАВКА о составе семьи",
    }
    text_map = {
        "school":  f"Настоящим подтверждается, что {child_name}\n"
                   f"является учеником МОУ «Школа №777» и обучается\n"
                   f"в 8-Б классе на 2025/26 учебный год.",
        "family":  f"Настоящим подтверждается, что {child_name}\n"
                   f"проживает в семье совместно с родителями\n"
                   f"Ивановым А.А. и Ивановой Б.Б.",
    }

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w/2, h - 100, title_map[cert_type])

    c.setFont("Helvetica", 12)
    for i, line in enumerate(text_map[cert_type].split("\n"), start=1):
        c.drawString(80, h - 120 - i*20, line)

    c.drawString(80, 120, f"Дата выдачи: {date.today().strftime('%d.%m.%Y')}")
    c.drawString(w - 200, 120, "Директор _________ /Сидорова Н.Н./")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer 