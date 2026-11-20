"""
PDF "Plant Health Report" generator.

Every report is drawn from the same fixed template (header band, scan image,
scan details, diagnosis, treatment plan, action checklist, disclaimer) so all
downloaded PDFs look identical apart from their data.
"""
import io
import os
from datetime import timezone

from fpdf import FPDF
from PIL import Image

from backend.disease_data import get_disease_info

# Theme colours (match style.css)
GREEN = (46, 125, 50)
GREEN_DARK = (27, 94, 32)
GREEN_LIGHT = (232, 245, 233)
BORDER = (200, 230, 201)
TEXT = (38, 50, 56)
MUTED = (110, 110, 110)
WARN_BG = (255, 243, 205)
WARN_TEXT = (122, 91, 0)

TREATMENT_ORDER = {"Cultural": 0, "Organic": 1, "Chemical": 2}


def _safe(text) -> str:
    """Core PDF fonts only support Latin-1, so swap common Unicode punctuation."""
    text = str(text or "-")
    for a, b in {"–": "-", "—": "-", "•": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "…": "..."}.items():
        text = text.replace(a, b)
    return text.encode("latin-1", "replace").decode("latin-1")


class _ReportPDF(FPDF):
    report_id = ""
    subtitle = "Plant Health Report"

    def header(self):
        self.set_fill_color(*GREEN)
        self.rect(0, 0, self.w, 28, "F")
        self.set_xy(15, 8)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 18)
        self.cell(0, 8, "PlantCare ML")
        self.set_xy(15, 16)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, self.subtitle)
        self.set_xy(-75, 11)
        self.set_font("Helvetica", "B", 10)
        self.cell(60, 6, self.report_id, align="R")
        self.set_y(36)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(*BORDER)
        self.line(15, self.get_y(), self.w - 15, self.get_y())
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 8, "DBMS Project - Plant Disease Detection Using Machine Learning")
        self.cell(0, 8, f"Page {self.page_no()} of {{nb}}", align="R")

    def section_title(self, title):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*GREEN_DARK)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*GREEN)
        self.set_line_width(0.6)
        self.line(15, self.get_y(), 60, self.get_y())
        self.set_line_width(0.2)
        self.ln(3)

    def key_value(self, key, value, x, width):
        self.set_x(x)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*GREEN_DARK)
        self.cell(width * 0.4, 6.2, _safe(key))
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*TEXT)
        self.multi_cell(width * 0.6, 6.2, _safe(value), align="L", new_x="LMARGIN", new_y="NEXT")

    def paragraph(self, label, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*GREEN_DARK)
        self.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*TEXT)
        self.multi_cell(0, 5.5, _safe(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)


def _image_as_jpeg(path: str):
    """Normalise any uploaded image to an RGB JPEG buffer (or None if unreadable)."""
    try:
        with Image.open(path) as img:
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=90)
            buf.seek(0)
            return buf, img.width, img.height
    except Exception:
        return None


def build_report(record, user, upload_dir: str) -> bytes:
    """Render the PDF report for one PredictionRecord and return its bytes."""
    info = get_disease_info(record.predicted_label)
    healthy = "healthy" in record.disease_name.lower()
    scanned = record.created_at.replace(tzinfo=timezone.utc) if record.created_at else None

    pdf = _ReportPDF(format="A4")
    pdf.report_id = f"Report #PC-{record.prediction_id:06d}"
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(True, margin=20)
    pdf.alias_nb_pages()
    pdf.add_page()

    # --- Image (left) + scan details (right) ---
    top = pdf.get_y()
    box_w, box_h = 75, 75
    pdf.set_draw_color(*BORDER)
    pdf.set_fill_color(*GREEN_LIGHT)
    pdf.rect(15, top, box_w, box_h, "DF")
    image = _image_as_jpeg(os.path.join(upload_dir, record.image_filename))
    if image:
        buf, iw, ih = image
        scale = min((box_w - 4) / iw, (box_h - 4) / ih)
        w, h = iw * scale, ih * scale
        pdf.image(buf, x=15 + (box_w - w) / 2, y=top + (box_h - h) / 2, w=w, h=h)
    else:
        pdf.set_xy(15, top + box_h / 2 - 4)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*MUTED)
        pdf.cell(box_w, 8, "Image not available", align="C")

    details_x, details_w = 15 + box_w + 8, pdf.w - 15 - (15 + box_w + 8)
    pdf.set_xy(details_x, top)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*GREEN_DARK)
    pdf.cell(details_w, 8, "Scan Details", new_x="LMARGIN", new_y="NEXT")
    rows = [
        ("Prepared for", f"{user.name} ({user.email})"),
        ("Scan date", scanned.strftime("%d %b %Y, %H:%M UTC") if scanned else "-"),
        ("Scan ID", str(record.prediction_id)),
        ("Plant", record.plant_name),
        ("Predicted disease", record.disease_name),
        ("Confidence", f"{record.confidence:.2f}%"),
        ("Pathogen type", info.get("pathogen", "-")),
    ]
    notes = (getattr(record, "notes", None) or "").strip()
    if notes and len(notes) <= 140:
        rows.append(("Farmer's notes", notes))
    for key, value in rows:
        pdf.key_value(key, value, details_x, details_w)

    # Confidence bar
    pdf.set_x(details_x)
    bar_y = pdf.get_y() + 2
    pdf.set_fill_color(224, 224, 224)
    pdf.rect(details_x, bar_y, details_w, 3, "F")
    pdf.set_fill_color(*GREEN)
    pdf.rect(details_x, bar_y, details_w * max(0, min(record.confidence, 100)) / 100, 3, "F")
    pdf.set_y(max(top + box_h, bar_y + 3) + 6)

    # --- Diagnosis banner ---
    if healthy:
        bg, fg, title = GREEN_LIGHT, GREEN_DARK, "Diagnosis: Healthy leaf"
        msg = f"No signs of disease were detected on this {record.plant_name} leaf. Keep following good crop care."
    else:
        bg, fg, title = WARN_BG, WARN_TEXT, f"Diagnosis: {record.disease_name} detected"
        msg = "Follow the treatment plan below and re-scan the plant after treatment to track recovery."
    pdf.set_fill_color(*bg)
    pdf.set_text_color(*fg)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, _safe("  " + title), fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.multi_cell(0, 5.5, _safe("  " + msg), fill=True, new_x="LMARGIN", new_y="NEXT")
    if record.confidence < 60:
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 5.5, _safe(
            "  Low confidence: retake a clear, well-lit photo of a single leaf for a more reliable result."),
            fill=True, new_x="LMARGIN", new_y="NEXT")

    # --- Disease information ---
    pdf.section_title("About This Condition")
    pdf.paragraph("Symptoms", info.get("symptoms"))
    pdf.paragraph("Prevention", info.get("prevention"))

    # --- Treatment plan ---
    pdf.section_title("Recommended Treatment Plan")
    treatments = sorted(info.get("treatments", []), key=lambda t: TREATMENT_ORDER.get(t[0], 9))
    for i, (kind, text) in enumerate(treatments, start=1):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*GREEN)
        pdf.cell(8, 6, f"{i}.")
        pdf.set_text_color(*GREEN_DARK)
        pdf.cell(0, 6, _safe(f"{kind} treatment"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(23)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*TEXT)
        pdf.multi_cell(0, 5.5, _safe(text), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1.5)

    # --- Action checklist (same steps on every report) ---
    pdf.section_title("Action Checklist")
    steps = [
        "Isolate or mark the affected plant to limit spread.",
        "Remove and safely dispose of badly infected leaves (do not compost).",
        "Apply the recommended treatment, starting with the least toxic option.",
        "Re-scan the plant in 7-10 days with PlantCare ML to check progress.",
    ] if not healthy else [
        "Continue regular watering at the soil line and balanced fertilisation.",
        "Inspect leaves weekly, especially after humid or rainy weather.",
        "Re-scan any leaf that develops spots, yellowing or lesions.",
    ]
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*TEXT)
    pdf.set_draw_color(*GREEN)
    for step in steps:
        y = pdf.get_y()
        pdf.rect(17, y + 1.2, 3.5, 3.5)
        pdf.set_x(24)
        pdf.multi_cell(0, 6, _safe(step), new_x="LMARGIN", new_y="NEXT")

    # --- Farmer's own notes (only when added) ---
    if len(notes) > 140:
        if pdf.get_y() > pdf.h - 60:
            pdf.add_page()
        pdf.section_title("Farmer's Notes")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*TEXT)
        pdf.multi_cell(0, 5.5, _safe(record.notes), new_x="LMARGIN", new_y="NEXT")

    _disclaimer(pdf)
    return bytes(pdf.output())


def _disclaimer(pdf):
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(0, 4.5, _safe(
        "This report is generated automatically by a machine learning model and is intended as guidance only. "
        "Always read pesticide labels and consult a local agricultural expert before applying chemical treatments."),
        new_x="LMARGIN", new_y="NEXT")


def _fmt(dt, pattern="%d %b %Y"):
    return dt.strftime(pattern) if dt else "-"


def _health_chart(pdf, logs, x, y, w, h):
    """Line chart of health scores (1-5) drawn with plain PDF lines."""
    pdf.set_draw_color(224, 224, 224)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*MUTED)
    for score in range(1, 6):
        gy = y + (5 - score) * h / 4
        pdf.line(x, gy, x + w, gy)
        pdf.set_xy(x - 6, gy - 2)
        pdf.cell(4, 4, str(score), align="R")
    if len(logs) < 2:
        pdf.set_xy(x, y + h / 2 - 3)
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(w, 6, "Add at least two health logs to see the chart.", align="C")
        return
    points = [(x + i * w / (len(logs) - 1), y + (5 - l.health_score) * h / 4) for i, l in enumerate(logs)]
    pdf.set_draw_color(*GREEN)
    pdf.set_line_width(0.8)
    for a, b in zip(points, points[1:]):
        pdf.line(a[0], a[1], b[0], b[1])
    pdf.set_line_width(0.2)
    pdf.set_fill_color(*GREEN_DARK)
    step = max(1, len(logs) // 6)
    for i, (px, py) in enumerate(points):
        pdf.ellipse(px - 1.2, py - 1.2, 2.4, 2.4, "F")
        if i % step == 0 or i == len(points) - 1:
            pdf.set_xy(px - 10, y + h + 1.5)
            pdf.cell(20, 4, _fmt(logs[i].logged_at, "%d %b"), align="C")


def build_plant_report(plant, summary, scans, user, upload_dir: str) -> bytes:
    """Render the multi-scan summary PDF for one tracked plant (same template as scan reports)."""
    logs = plant.logs
    pdf = _ReportPDF(format="A4")
    pdf.report_id = f"Plant Summary #PC-P{plant.tracked_id:05d}"
    pdf.subtitle = "Plant Health Summary"
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(True, margin=20)
    pdf.alias_nb_pages()
    pdf.add_page()

    # --- Plant details ---
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*GREEN_DARK)
    pdf.cell(0, 8, _safe(f"{plant.nickname} ({plant.crop})"), new_x="LMARGIN", new_y="NEXT")
    trend_text = {"new": "New", "improving": "Improving", "declining": "Declining", "stable": "Stable"}
    first, last = (logs[0], logs[-1]) if logs else (None, None)
    rows = [
        ("Prepared for", f"{user.name} ({user.email})"),
        ("Tracking since", _fmt(plant.created_at)),
        ("Health logs", f"{len(logs)} (latest score {last.health_score}/5)" if last else "None yet"),
        ("Trend", trend_text.get(summary["trend"], summary["trend"])),
        ("Linked scans", str(len(scans))),
        ("Period covered", f"{_fmt(first.logged_at)} - {_fmt(last.logged_at)}" if logs else "-"),
    ]
    for key, value in rows:
        pdf.key_value(key, value, 15, pdf.w - 30)

    # --- Recommendation banner (same style as the diagnosis banner) ---
    pdf.ln(3)
    declining = summary["trend"] == "declining"
    bg, fg = (WARN_BG, WARN_TEXT) if declining else (GREEN_LIGHT, GREEN_DARK)
    pdf.set_fill_color(*bg)
    pdf.set_text_color(*fg)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "  Recommendation", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.multi_cell(0, 5.5, _safe("  " + summary["recommendation"]), fill=True, new_x="LMARGIN", new_y="NEXT")

    # --- Health chart ---
    pdf.section_title("Health Over Time")
    top = pdf.get_y() + 2
    _health_chart(pdf, logs, 25, top, pdf.w - 45, 45)
    pdf.set_y(top + 55)

    # --- Log table ---
    pdf.section_title("Health Log")
    if not logs:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 6, "No health logs yet.", new_x="LMARGIN", new_y="NEXT")
    else:
        widths = [28, 18, 60, pdf.w - 30 - 106]
        pdf.set_fill_color(*GREEN_LIGHT)
        pdf.set_text_color(*GREEN_DARK)
        pdf.set_font("Helvetica", "B", 9)
        for head, wd in zip(["Date", "Score", "Observations", "Notes"], widths):
            pdf.cell(wd, 7, head, border="B", fill=True)
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*TEXT)
        labels = {"leaf_spots": "spots", "yellowing": "yellowing", "wilting": "wilting",
                  "pests": "pests", "watered": "watered", "treated": "treated"}
        line_h = 5
        for l in reversed(logs):
            obs = ", ".join(v for k, v in labels.items() if getattr(l, k)) or "-"
            row = [_fmt(l.logged_at), f"{l.health_score}/5", obs, l.notes or "-"]
            # Use the tallest cell so long notes wrap without breaking the row
            lines = max(len(pdf.multi_cell(wd, line_h, _safe(v), dry_run=True, output="LINES"))
                        for v, wd in zip(row, widths))
            if pdf.get_y() + lines * line_h > pdf.h - 25:
                pdf.add_page()
            y0 = pdf.get_y()
            xpos = 15
            for v, wd in zip(row, widths):
                pdf.set_xy(xpos, y0)
                pdf.multi_cell(wd, line_h, _safe(v))
                xpos += wd
            pdf.set_y(y0 + lines * line_h + 1)
            pdf.set_draw_color(*BORDER)
            pdf.line(15, pdf.get_y(), pdf.w - 15, pdf.get_y())
            pdf.ln(1)

    # --- Linked scans with thumbnails ---
    pdf.section_title("Linked Leaf Scans")
    if not scans:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(0, 5.5, "No scans are linked to this plant yet. Choose this plant when scanning a leaf "
                               "to include the scan here.", new_x="LMARGIN", new_y="NEXT")
    for scan in reversed(scans):
        if pdf.get_y() + 30 > pdf.h - 25:
            pdf.add_page()
        y0 = pdf.get_y()
        pdf.set_draw_color(*BORDER)
        pdf.set_fill_color(*GREEN_LIGHT)
        pdf.rect(15, y0, 26, 26, "DF")
        image = _image_as_jpeg(os.path.join(upload_dir, scan.image_filename))
        if image:
            buf, iw, ih = image
            scale = min(24 / iw, 24 / ih)
            pdf.image(buf, x=15 + (26 - iw * scale) / 2, y=y0 + (26 - ih * scale) / 2, w=iw * scale, h=ih * scale)
        info = get_disease_info(scan.predicted_label)
        pdf.set_xy(46, y0)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*GREEN_DARK)
        pdf.cell(0, 6, _safe(f"{scan.disease_name}  -  {scan.confidence:.1f}%"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(46)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 5, _safe(f"Scan #{scan.prediction_id} on {_fmt(scan.created_at, '%d %b %Y, %H:%M')} UTC"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(46)
        pdf.set_text_color(*TEXT)
        first_treatment = (info.get("treatments") or [("", "-")])[0]
        pdf.multi_cell(0, 5, _safe(f"Suggested: {first_treatment[1]}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_y(max(pdf.get_y(), y0 + 26) + 4)

    _disclaimer(pdf)
    return bytes(pdf.output())
