"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import qpl_constants as C
from qpl_evaluation import Settings, de, num, padtext, pct

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "Δ": "Delta", "↔": "<->", "„": '"', "“": '"', "²": "2", "³": "3", "⁻": "-", "¹": "1", "½": "1/2", "⁴": "4"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, v: dict) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Quadratische Platzierung: relaxierte Orte"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    inst = v["inst"]
    how = "alle Anordnungen aufgezählt" if v["exact"] else "nicht aufgezählt, beste von 100 Abstiegen als Vergleich (obere Grenze)"
    pdf.multi_cell(0, 5, _s(f"Familie {C.FAMILY_NAMES[s.family]}, {s.n} Bauteile, {inst.rows}x{inst.cols}-Raster, Seed {s.seed}; {padtext(s.pads)}, Pad-Gewicht x{s.factor:g}; {s.reweights} Umgewichtungen; {how}. "
                            "Eine Instanz, kein Befund über die Familie. Erfundene Pads, einfache Fassungen. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    q, b = v["q"], v["b"]
    ref_name = "Optimum (aufgezählt)" if v["exact"] else "Beste gefundene Lösung (obere Grenze)"
    rows = [(ref_name, num(v["ref"])), ("Rundung, quadratisch (Kosten)", num(q["cost"])), ("Lücke, quadratisch", pct(q["gap"], 1)), ("Streuung der stetigen Orte, quadratisch", de(q["spread"], 2)),
            ("Überlappung (Bauteile mit gleichem nächsten Platz)", q["overlap"]), (f"Rundung nach {s.reweights} Umgewichtungen (Kosten)", num(b["cost"])), ("Lücke, umgewichtet", pct(b["gap"], 1)),
            ("Streuung, umgewichtet", de(b["spread"], 2)), ("Stetige Länge, umgewichtet / quadratisch", pct(b["length"] / q["length"]) if q["length"] else "-")]
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(110, 6, "Kennzahl", border=1)
    pdf.cell(75, 6, "Wert", border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for k, val in rows:
        pdf.cell(110, 5.5, _s(k), border=1)
        pdf.cell(75, 5.5, _s(val)[:50], border=1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Quelle: quadratische-platzierung-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
