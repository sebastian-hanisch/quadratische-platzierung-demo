"""Abbildungen: sie entstehen für jede Eingabe, Achsen sind gesperrt, Beschriftungen und Daten stimmen mit den Werten überein; PDF-Export."""

import qpl_constants as C
import qpl_evaluation as ev
import qpl_instance as I
import qpl_visualization as V
from qpl_pdf_export import build_pdf


def _locked(fig):
    return fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_positions_chart_shows_slots_pads_links_and_the_continuous_points():
    for p in (0, 4):
        s = ev.Settings("netlist", 6, 35, p)
        v = ev.instance_data(s)
        fig = V.build_positions(v["inst"], v["pads"], v["q"]["X"], v["q"]["perm"], "Test")
        names = [t.name for t in fig.data]
        assert names[0] == "Plätze" and names[-1] == "stetige Orte" and "Rundung auf den Platz" in names and (("Pads (fest)" in names) == (p > 0)) and _locked(fig)
        assert list(fig.data[-1].text) == list(v["inst"].names) and len(fig.data[-1].x) == 6


def test_arrangement_chart(land6):
    inst, ls = land6
    fig = V.build_arrangement(inst, [int(x) for x in ls.optima[0]], "Anordnung")
    assert len(fig.data[-1].x) == 6 and list(fig.data[-1].text) == list(inst.names) and _locked(fig)
    for fam in C.FAMILIES:
        for n in (6, 9, 12, 16):
            assert len(V.build_arrangement(I.make_instance(fam, n, 3), list(range(n)), fam).data[-1].x) == n


def test_curve_charts_carry_the_curve_values():
    s = ev.Settings("uniform", 6, 100000)
    v = ev.instance_data(s)
    pc, fc, rc = ev.pads_curve(s), ev.factor_curve(s), ev.reweight_curve(s, v)
    f1 = V.build_pads_curve(pc)
    assert list(f1.data[0].x) == [str(c["p"]) for c in pc] and list(f1.data[0].y) == [c["spread"] for c in pc] and list(f1.data[1].y) == [100 * c["gap"] for c in pc]
    f2 = V.build_factor_curve(fc)
    assert list(f2.data[0].x) == [f"×{c['factor']:g}" for c in fc] and list(f2.data[1].y) == [100 * c["gap"] for c in fc]
    f3 = V.build_reweight_curve(rc)
    assert len(f3.data) == 3 and list(f3.data[0].y) == [c["length"] for c in rc] and list(f3.data[2].y) == [100 * c["gap"] for c in rc]


def test_sweep_charts():
    rows = [r for f in C.FAMILIES for r in ev.sweep_pads(f, 6, (100000, 100001), (0, 4, 8))]
    g = V.build_gap_bars(rows, ev.median_of, "t")
    assert [t.name for t in g.data] == ["0 Pads", "4 Pads", "8 Pads"] and len(g.data[0].x) == 6 and _locked(g)
    m = V.build_method_bars(rows, ev.median_of, "t")
    assert [t.name for t in m.data][:2] == ["quadratisch", f"umgewichtet ({C.DEFAULT_REWEIGHTS} Schritte)"] and len(m.data) == 3 and list(m.data[0].x) == ["0", "4", "8"]
    big = [dict(r, exact=False) for r in rows]
    assert len(V.build_method_bars(big, ev.median_of, "t").data) == 2
    sc = V.build_spread_scatter(rows, "t")
    assert [t.name for t in sc.data] == ["0 Pads", "4 Pads", "8 Pads"] and all(len(t.x) == 12 for t in sc.data)


def test_the_pdf_export_returns_a_pdf_for_an_exact_and_a_large_instance():
    s = ev.Settings("netlist", 6, 35)
    assert build_pdf(s, ev.instance_data(s))[:5] == b"%PDF-"
    s2 = ev.Settings("uniform", 12, 35, 0, 4.0, 2)
    data = build_pdf(s2, ev.instance_data(s2))
    assert data[:5] == b"%PDF-" and len(data) > 1500
