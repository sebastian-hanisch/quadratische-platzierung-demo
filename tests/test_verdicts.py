"""Verdikte (reine Funktionen in qpl_evaluation.py) an handgesetzten Werten: Art, Schwellen und jede Zahl im Text (DEMO-PLAYBOOK §1b)."""

import numpy as np

import qpl_evaluation as ev


def _res(cost, gap, spread=0.5, overlap=4, length=100.0):
    return {"X": np.zeros((8, 2)), "perm": list(range(8)), "cost": cost, "gap": gap, "spread": spread, "overlap": overlap, "length": length, "qvalue": 1.0}


def _v(q, b, ref=50.0, exact=True, mean=70.0, n=8):
    inst = type("I", (), {"rows": 2, "cols": 4})()
    return {"inst": inst, "exact": exact, "ref": ref, "mean": mean, "gap_mean": (mean - ref) / ref if mean else None, "q": q, "b": b}


def _row(p, gq=0.1, gb=0.08, mean=0.3, hq=False, hb=False, sq=0.4, sb=0.1, ov=4, ratio=1.2, better=False, worse=False, exact=True):
    return {"family": "netlist", "p": p, "gap_q": gq, "gap_b": gb, "gap_mean": mean, "hit_q": hq, "hit_b": hb, "spread_q": sq, "spread_b": sb, "overlap_q": ov, "length_ratio": ratio, "b_better": better, "b_worse": worse, "exact": exact,
            "factor": 1.0, "family_": "x", "seed": 1}


def test_system_verdict_with_pads_without_pads_and_for_a_large_instance():
    s = ev.Settings("netlist", 8, 35, 4, 1.0, 5)
    v = _v(_res(55, 0.10, 0.4, 4), _res(54, 0.08, 0.1, 5, 80.0))
    kind, text = ev.verdict_system(s, v)
    assert kind == "success" and "Familie **Netzliste**, 8 Bauteile, Raster 2×4, Seed 35, 4 Pads, Pad-Gewicht ×1" in text and "0,40 der Streuung der Plätze, 4 von 8 Bauteilen" in text and "**55** gegen das aufgezählte Optimum 50 (Lücke **10,0 %**; mittlere Kosten aller Anordnungen 40,0 % über dem Optimum)" in text
    assert "Nach 5 Umgewichtungen: Streuung 0,10, stetige Länge 80 % der quadratischen Lösung, Kosten 54 (Lücke 8,0 %)" in text
    assert ev.verdict_system(s, _v(_res(60, 0.20), _res(60, 0.2)))[0] == "info"
    k0, t0 = ev.verdict_system(ev.Settings(pads=0), _v(_res(79, 0.58, 0.0, 7), _res(79, 0.58, 0.0, 7)))
    assert k0 == "warning" and "ohne Pads ist das System singulär, **alle 8 Bauteile liegen auf demselben Punkt** (Streuung 0,00, 7 von 8 Bauteilen" in t0 and "Kosten 79 gegen das aufgezählte Optimum 50 (Lücke 58,0 %; die mittleren Kosten aller Anordnungen liegen 40,0 % darüber)" in t0
    big = _v(_res(106, 0.269, 0.21, 10), _res(98, 0.18, 0.03, 10, 70.0), ref=83.5, exact=False, mean=None)
    assert "die beste von 100 Abstiegen (obere Grenze) 83,5" in ev.verdict_system(ev.Settings(n=12), big)[1] and "mittlere Kosten" not in ev.verdict_system(ev.Settings(n=12), big)[1]
    assert "Pad-Gewicht ×0,25" in ev.verdict_system(ev.Settings(factor=0.25), v)[1]


def test_collapse_factor_and_reweight_verdicts():
    s = ev.Settings(pads=4)
    pc = [{"p": 0, "spread": 0.0, "overlap": 7, "gap": 0.58, "ref": 31}, {"p": 2, "spread": 0.53, "overlap": 6, "gap": 0.044, "ref": 40}]
    kind, text = ev.verdict_collapse(s, pc)
    assert kind == "info" and "0 Pads: Streuung 0,00, Überlappung 7, Lücke 58,0 %; 2 Pads: Streuung 0,53, Überlappung 6, Lücke 4,4 %" in text
    fc = [{"factor": 0.25, "spread": 0.27, "overlap": 5, "gap": 0.095, "ref": 1}, {"factor": 4.0, "spread": 1.21, "overlap": 3, "gap": 0.01, "ref": 1}]
    text = ev.verdict_factor(s, fc)[1]
    assert "×0,25: Streuung 0,27, Lücke 9,5 %; ×4: Streuung 1,21, Lücke 1,0 %" in text and "4 Pads" in text
    rc = [{"reweights": 0, "length": 1.0, "spread": 0.69, "overlap": 4, "gap": 0.05}, {"reweights": 5, "length": 0.8, "spread": 0.33, "overlap": 5, "gap": 0.02}, {"reweights": 20, "length": 0.79, "spread": 0.31, "overlap": 5, "gap": 0.03}]
    text = ev.verdict_reweight(s, rc)[1]
    assert "0: Länge 100 %, Streuung 0,69, Lücke 5,0 %" in text and "Die Länge sinkt auf 79 %, die Streuung von 0,69 auf 0,31" in text and "die kleinste Lücke nach der Rundung gibt es bei 5 Umgewichtungen (2,0 %)" in text
    assert "ändert die Umgewichtung nichts" in ev.verdict_reweight(ev.Settings(pads=0), rc)[1]


def test_sweep_pads_verdict_counts():
    rows = [_row(0, gq=0.39, mean=0.42, sq=0.0), _row(0, gq=0.39, mean=0.42, sq=0.0), _row(4, gq=0.09, hq=True, better=True), _row(4, gq=0.10, worse=True), _row(8, gq=0.06, hb=True, better=True), _row(8, gq=0.06, better=True)]
    kind, text = ev.verdict_sweep_pads(8, rows)
    assert kind == "info" and "Bei n = 8, Median der Lücke der quadratischen Platzierung über 2 Instanzen je Zahl der Pads" in text and "0 Pads: 39,0 % (Zufall 42 %); 4 Pads: 9,5 % (Zufall 30 %); 8 Pads: 6,0 % (Zufall 30 %)" in text
    assert "4 Pads: besser in 1, schlechter in 1 von 2; 8 Pads: besser in 2, schlechter in 0 von 2" in text and "treffen quadratisch 0, 1, 0 und umgewichtet 0, 0, 1 Instanzen (0, 4, 8 Pads)" in text and "obere Grenze" not in text
    assert "obere Grenze der Lücke" in ev.verdict_sweep_pads(12, [_row(4, exact=False, mean=float("nan"))])[1]


def test_sweep_factor_and_reweight_verdicts():
    rows = [dict(_row(4), factor=f, gap_q=g, spread_q=sp, seed=s_) for s_ in (1, 2) for f, g, sp in ((0.25, 0.15, 0.1), (1.0, 0.08, 0.3))]
    text = ev.verdict_sweep_factor(rows)[1]
    assert "2 Instanzen mit 4 Pads, Median: ×0,25: Lücke 15,0 %, Streuung 0,10; ×1: Lücke 8,0 %, Streuung 0,30" in text
    rr = [{"family": "netlist", "seed": s_, "reweights": k, "gap": g, "spread": sp, "length": ln} for s_ in (1, 2) for k, g, sp, ln in ((0, 0.08, 0.3, 1.0), (5, 0.09, 0.07, 0.79))]
    assert "2 Instanzen, Median: 0: Lücke 8,0 %, Streuung 0,30, Länge 100 %; 5: Lücke 9,0 %, Streuung 0,07, Länge 79 %" in ev.verdict_sweep_reweights(rr)[1]


def test_core_verdict_quotes_the_numbers():
    s = ev.Settings()
    v = _v(_res(55, 0.10, 0.4, 4), _res(54, 0.08, 0.1, 5, 80.0))
    text = ev.verdict_core(s, v)[1]
    assert "Lücke 10,0 % gegen das aufgezählte Optimum, Streuung 0,40, Überlappung 4 von 8" in text and "Ohne Pads wäre es ein Punkt" in text and "Experiment 1 bis 5" in text
    assert "Hier gibt es keine Pads" in ev.verdict_core(ev.Settings(pads=0), v)[1]
