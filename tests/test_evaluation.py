"""Zeilen für die Vergleiche, Zusammenfassungen und Instanzdaten: Handwerte und Eigenschaften."""

import math

import numpy as np
import pytest

import qpl_constants as C
import qpl_evaluation as ev
import qpl_instance as I
import qpl_place as Pl


def test_helpers():
    assert ev.de(-1.5, 1) == "−1,5" and ev.pct(0.266, 1) == "26,6 %" and ev.fam("star") == "Stern" and ev.num(27.0) == "27" and ev.num(26.5) == "26,5" and ev.padtext(0) == "ohne Pads" and ev.padtext(4) == "4 Pads"
    assert ev.rel(110, 100) == pytest.approx(0.1) and math.isnan(ev.rel(5, 0)) and ev.rel(100 + 1e-14, 100) == 0.0
    assert ev.median_of([{"v": 1}, {"v": 5}, {"v": 2}], "v") == 2.0


def test_instance_data_for_an_enumerated_size(land6):
    inst, ls = land6
    s = ev.Settings("netlist", 6, 35)
    v = ev.instance_data(s)
    q, b = v["q"], v["b"]
    assert v["exact"] and v["ref"] == Pl.reference(inst, v["c"], 35)[0] and q["gap"] >= 0 and b["gap"] >= 0 and sorted(q["perm"]) == list(range(6)) and sorted(v["ref_perm"]) == list(range(6))
    assert q["cost"] == pytest.approx(Pl.cost_of(q["perm"], inst.F, inst.D, v["c"])) and v["gap_mean"] > q["gap"] and q["qvalue"] <= Pl.quadratic_value(inst, b["X"], v["pads"]) + 1e-9
    assert b["length"] <= q["length"] + 1e-9 and 0 <= q["spread"] and 0 <= q["overlap"] <= 5


def test_instance_data_without_pads_and_for_a_large_size():
    v0 = ev.instance_data(ev.Settings(pads=0))
    assert v0["q"]["spread"] == pytest.approx(0.0, abs=1e-12) and v0["q"]["overlap"] == 7 and v0["b"]["spread"] == pytest.approx(0.0, abs=1e-12)
    v12 = ev.instance_data(ev.Settings("sparse", 12, 100000, 4))
    assert not v12["exact"] and v12["mean"] is None and v12["gap_mean"] is None and v12["ref"] > 0 and sorted(v12["ref_perm"]) == list(range(12))


def test_curves_have_one_point_per_choice():
    s = ev.Settings("uniform", 6, 100000)
    v = ev.instance_data(s)
    pc, fc, rc = ev.pads_curve(s), ev.factor_curve(s), ev.reweight_curve(s, v)
    assert [c["p"] for c in pc] == list(C.PAD_CHOICES) and [c["factor"] for c in fc] == list(C.FACTOR_CHOICES) and [c["reweights"] for c in rc] == list(C.REWEIGHT_CHOICES)
    assert pc[0]["spread"] == pytest.approx(0.0, abs=1e-12) and pc[0]["overlap"] == 5 and [c["spread"] for c in fc] == sorted(c["spread"] for c in fc)
    assert rc[0]["length"] == pytest.approx(1.0) and all(rc[i + 1]["length"] <= rc[i]["length"] + 1e-6 for i in range(len(rc) - 1)) and rc[-1]["length"] < 1.0


def test_row_of_and_summaries():
    rows = ev.sweep_pads("sparse", 6, (100000, 100001, 100002), (0, 4))
    assert len(rows) == 6 and {r["p"] for r in rows} == {0, 4} and all(r["exact"] and r["ref"] > 0 for r in rows)
    r = rows[1]
    inst = I.make_instance("sparse", 6, 100000)
    pads = Pl.make_pads(inst, 4, 100000)
    assert r["ref"] == Pl.reference(inst, Pl.linear_costs(inst, pads), 100000)[0] and r["gap_q"] >= 0 and 0 <= r["spread_q"]
    sm = ev.pad_summary(rows, 4)
    assert sm["count"] == 3 and sm["gap_q"] == float(np.median([x["gap_q"] for x in rows if x["p"] == 4])) and sm["hit_q"] <= 3 and sm["b_better"] + sm["b_worse"] <= 3
    assert ev.pad_summary(rows, 0)["spread_q"] == pytest.approx(0.0, abs=1e-12)
    assert len(ev.pooled({"sparse": rows, "star": rows})) == 12 and ev.family_gap(rows, "sparse", 4) == sm["gap_q"]


def test_factor_and_reweight_sweeps():
    fr = ev.sweep_factor("star", 6, (100000, 100001))
    assert len(fr) == 2 * len(C.FACTOR_CHOICES) and {r["factor"] for r in fr} == set(C.FACTOR_CHOICES)
    rr = ev.sweep_reweights("star", 6, (100000, 100001), 4)
    assert len(rr) == 2 * len(C.REWEIGHT_CHOICES) and {r["reweights"] for r in rr} == set(C.REWEIGHT_CHOICES) and all(r["p"] == 4 and r["family"] == "star" for r in rr)


def test_hand_data():
    h = ev.hand_data()
    assert h["x"] == pytest.approx([-1 / 11, 3 / 11, 23 / 11], abs=1e-5) and h["perm"] == [0, 1, 2] and h["cost"] == 10.0 and h["opt"] == 10.0
