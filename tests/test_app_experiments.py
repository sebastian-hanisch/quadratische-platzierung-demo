"""Pfade der App, die der Rauchtest nicht erreicht: die Experimente im Seiteninhalt, PDF, jede Familie, jede Pad-Zahl, große Instanzen, die Rechenknöpfe (DEMO-PLAYBOOK §1d)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

import qpl_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
KIND = {"family_select": "selectbox", "n_select": "select_slider", "seed_input": "number_input", "pads_select": "select_slider", "factor_select": "select_slider", "reweights_select": "select_slider"}


def _app(**state) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    for key, value in state.items():
        getattr(at.sidebar, KIND[key])(key=key).set_value(value)
    if state:
        at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join(str(e.value) for e in list(at.success) + list(at.info) + list(at.warning) + list(at.error) + list(at.markdown))


def test_default_page_shows_the_metrics_and_the_verdicts():
    at = _app()
    values = {m.label: m.value for m in at.metric}
    assert set(values) == {"Lücke, quadratisch", "Lücke, 5 Umgewichtungen", "Streuung der stetigen Orte", "Optimum", "Pads"}
    assert values["Pads"] == "4 Pads" and values["Optimum"] and values["Lücke, quadratisch"].endswith("%")
    text = _texts(at)
    for part in ("Familie **Netzliste**, 8 Bauteile, Raster 2×4, Seed 35, 4 Pads", "die quadratische Platzierung streut die Bauteile", "Gleiche Instanz, quadratische Platzierung: 0 Pads: Streuung 0,00", "Umgewichtungen (stetige Länge", "Experiment 1 bis 5"):
        assert part in text, part


def test_the_experiments_the_hand_example_the_limits_table_and_the_formulation_are_on_the_page():
    at = _app()
    headings = [s.value for s in at.subheader]
    assert [h.split(":")[0] for h in headings if h.startswith("🔬 Experiment")] == [f"🔬 Experiment {i}" for i in (1, 2, 3, 4, 5)] and "🚧 Wo die Annahmen enden" in headings
    assert [e.label for e in at.expander] == ["So funktioniert es", "Handbeispiel zum Nachrechnen", "📐 Mathematische Formulierung"]
    assert not at.error and len(at.get("plotly_chart")) == 7
    assert any("x_A = −1/11" in str(m.value) for m in at.markdown)


def test_every_family_every_pad_count_and_size_renders():
    for fam in C.FAMILIES:
        at = _app(family_select=fam, n_select=6)
        assert f"Familie **{C.FAMILY_NAMES[fam]}**" in _texts(at) and len(at.get("plotly_chart")) == 7
    for p in C.PAD_CHOICES:
        at = _app(pads_select=p, n_select=6)
        assert len(at.get("plotly_chart")) == (7 if p else 6) and not at.exception
    for n in (9, 12, 16):
        at = _app(n_select=n)
        assert f"{n} Bauteile" in _texts(at) and len(at.get("plotly_chart")) == 7


def test_without_pads_the_page_shows_the_collapse():
    at = _app(pads_select=0)
    text = _texts(at)
    assert "alle 8 Bauteile liegen auf demselben Punkt" in text and "Ohne Pads gibt es kein Pad-Gewicht" in text and "ändert die Umgewichtung nichts" in text
    assert {m.label: m.value for m in at.metric}["Streuung der stetigen Orte"] == "0,00"


def test_the_controls_change_the_result():
    base = {m.label: m.value for m in _app(n_select=6).metric}
    weak = {m.label: m.value for m in _app(n_select=6, factor_select=0.25).metric}
    assert base["Streuung der stetigen Orte"] != weak["Streuung der stetigen Orte"]
    r0 = _app(n_select=6, reweights_select=0)
    assert any(m.label == "Lücke, 0 Umgewichtungen" for m in r0.metric)


def test_the_pdf_button_makes_a_download():
    at = _app(n_select=6)
    at.button(key="pdf_make").click().run()
    assert not at.exception
    assert any(d.proto.label == "⬇️ PDF herunterladen" for d in at.get("download_button"))


def test_the_comparison_buttons_fill_their_sections(monkeypatch):
    monkeypatch.setattr(C, "SWEEP_SEEDS", C.SWEEP_SEEDS[:2])                       # nur für die Geschwindigkeit des Tests: die echten Reihen stehen in test_claims.py
    monkeypatch.setattr(C, "SWEEP_SEEDS_SMALL", C.SWEEP_SEEDS[:1])
    monkeypatch.setattr(C, "LARGE_SEEDS", C.SWEEP_SEEDS[:1])
    at = _app(n_select=6)
    assert [b.label for b in at.button if "⏱️" in b.label] == ["⏱️ Vergleich rechnen (n = 8)", "⏱️ Pad-Gewicht und Umgewichtungen rechnen (n = 8)", "⏱️ Große Instanzen rechnen (n = 12)"]
    at.button(key="sweep_button").click().run()
    assert not at.exception and "Bei n = 8, Median der Lücke der quadratischen Platzierung über 12 Instanzen je Zahl der Pads" in _texts(at) and len(at.get("plotly_chart")) == 7 + 2
    at.button(key="small_button").click().run()
    assert not at.exception and "Pad-Gewicht gegen das Grundgewicht, 6 Instanzen mit 4 Pads" in _texts(at) and "Zahl der Umgewichtungen, 6 Instanzen" in _texts(at)
    at.button(key="large_button").click().run()
    assert not at.exception and "Bei n = 12, Median der Lücke" in _texts(at) and "obere Grenze der Lücke" in _texts(at)
