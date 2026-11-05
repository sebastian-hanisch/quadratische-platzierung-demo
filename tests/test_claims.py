"""Die Zahlen der README (Abschnitte „Befunde“ und „Grenzen“) als Tests: Standardfall, Handbeispiel und die Vergleiche über feste Instanzen.
Prozentwerte auf eine Stelle (Toleranz 0,05), Zählungen exakt, Streuungen auf zwei Stellen; Zeiten stehen nie in Tests (DEMO-PLAYBOOK §1b, Wiederholbarkeit)."""

import numpy as np
import pytest

import qpl_constants as C
import qpl_evaluation as ev


def pc(x):
    return 100 * x


@pytest.fixture(scope="module")
def standard():
    s = ev.Settings()
    return s, ev.instance_data(s)


@pytest.fixture(scope="module")
def sweep8():
    return ev.pooled({f: ev.sweep_pads(f, C.SWEEP_N, C.SWEEP_SEEDS, C.PAD_CHOICES) for f in C.FAMILIES})


@pytest.fixture(scope="module")
def small8():
    parts = [(ev.sweep_factor(f, C.SWEEP_N, C.SWEEP_SEEDS_SMALL), ev.sweep_reweights(f, C.SWEEP_N, C.SWEEP_SEEDS_SMALL, 4), ev.sweep_reweights(f, C.SWEEP_N, C.SWEEP_SEEDS_SMALL, 8)) for f in C.FAMILIES]
    return [r for a, _, _ in parts for r in a], [r for _, b, _ in parts for r in b], [r for _, _, c in parts for r in c]


@pytest.fixture(scope="module")
def sweep12():
    return ev.pooled({f: ev.sweep_pads(f, C.LARGE_SWEEP_N, C.LARGE_SEEDS, (4, 8)) for f in C.FAMILIES})


def test_standard_instance_numbers(standard):
    s, v = standard
    q, b = v["q"], v["b"]
    assert (s.family, s.n, s.seed, s.pads, s.factor, s.reweights) == ("netlist", 8, 35, 4, 1.0, 5) and v["exact"]
    assert v["ref"] == 50.0 and q["cost"] == 51.0 and b["cost"] == 51.0 and pc(q["gap"]) == pytest.approx(2.0, abs=0.05) and pc(v["gap_mean"]) == pytest.approx(52.0, abs=0.05)
    assert q["spread"] == pytest.approx(0.69, abs=0.006) and q["overlap"] == 4 and b["spread"] == pytest.approx(0.33, abs=0.006) and b["overlap"] == 5 and pc(b["length"] / q["length"]) == pytest.approx(79.9, abs=0.06)


def test_standard_instance_curves(standard):
    s, v = standard
    exp = [(0, 0.0, 7, 58.1, 31.0), (2, 0.53, 6, 4.4, 45.0), (4, 0.69, 4, 2.0, 50.0), (8, 0.47, 4, 2.3, 88.5)]
    for c, (p, sp, ov, gap, ref) in zip(ev.pads_curve(s), exp):
        assert (c["p"], c["overlap"], c["ref"]) == (p, ov, ref) and c["spread"] == pytest.approx(sp, abs=0.006) and pc(c["gap"]) == pytest.approx(gap, abs=0.051)
    for c, (f, sp, gap) in zip(ev.factor_curve(s), [(0.25, 0.27, 9.5), (1.0, 0.69, 2.0), (4.0, 1.21, 1.0), (16.0, 1.66, 0.3)]):
        assert c["factor"] == f and c["spread"] == pytest.approx(sp, abs=0.006) and pc(c["gap"]) == pytest.approx(gap, abs=0.051)
    for c, (r, ln, sp, gap) in zip(ev.reweight_curve(s, v), [(0, 100.0, 0.69, 2.0), (1, 82.4, 0.46, 2.0), (2, 80.5, 0.38, 2.0), (5, 79.9, 0.33, 2.0), (10, 79.8, 0.31, 2.0), (20, 79.8, 0.31, 2.0)]):
        assert c["reweights"] == r and pc(c["length"]) == pytest.approx(ln, abs=0.06) and c["spread"] == pytest.approx(sp, abs=0.006) and pc(c["gap"]) == pytest.approx(gap, abs=0.051)


def test_hand_example():
    h = ev.hand_data()
    assert h["x"] == pytest.approx([-1 / 11, 3 / 11, 23 / 11], abs=1e-5) and h["perm"] == [0, 1, 2] and h["cost"] == 10.0 == h["opt"]


def test_n8_sweep_counts_and_pooled_gaps(sweep8):
    assert len(sweep8) == 480 and all(r["exact"] for r in sweep8) and not any(r["q_below"] for r in sweep8)
    exp = {0: (39.5, 39.5, 42.0, 0, 0, 0, 0, 7.0, 0.0), 2: (14.1, 12.7, 38.1, 3, 4, 43, 38, 6.0, 0.29), 4: (9.3, 9.6, 34.5, 5, 4, 44, 50, 4.0, 0.32), 8: (6.2, 4.3, 26.1, 5, 14, 61, 41, 4.0, 0.44)}
    for p, (gq, gb, mean, hq, hb, better, worse, ov, sp) in exp.items():
        sm = ev.pad_summary(sweep8, p)
        assert sm["count"] == 120 and pc(sm["gap_q"]) == pytest.approx(gq, abs=0.051) and pc(sm["gap_b"]) == pytest.approx(gb, abs=0.051) and pc(sm["gap_mean"]) == pytest.approx(mean, abs=0.051)
        assert (sm["hit_q"], sm["hit_b"], sm["b_better"], sm["b_worse"], sm["overlap_q"]) == (hq, hb, better, worse, ov) and sm["spread_q"] == pytest.approx(sp, abs=0.006)
    assert [ev.pad_summary(sweep8, p)["length_ratio"] for p in (2, 4, 8)] == pytest.approx([1.34, 1.23, 1.13], abs=0.006)
    assert [ev.pad_summary(sweep8, p)["spread_b"] for p in (2, 4, 8)] == pytest.approx([0.05, 0.08, 0.19], abs=0.006)


def test_n8_sweep_per_family(sweep8):
    """Je Familie auf ganze Prozent gerundet (Toleranz 0,51: einzelne Werte liegen nahe der Rundungsgrenze)."""
    q = {0: (44, 19, 94, 41, 19, 89), 2: (15, 7, 21, 15, 12, 32), 4: (11, 6, 9, 7, 12, 14), 8: (7, 4, 4, 6, 7, 10)}
    b8 = (6, 3, 3, 1, 7, 6)
    mean8 = {0: (41, 22, 83, 42, 37, 77), 8: (25, 20, 26, 26, 27, 43)}
    for p, vals in q.items():
        for f, x in zip(C.FAMILIES, vals):
            assert pc(ev.family_gap(sweep8, f, p)) == pytest.approx(x, abs=0.51), (p, f)
    for f, x in zip(C.FAMILIES, b8):
        assert pc(ev.family_gap(sweep8, f, 8, "gap_b")) == pytest.approx(x, abs=0.51), f
    for p, vals in mean8.items():
        for f, x in zip(C.FAMILIES, vals):
            assert pc(ev.family_gap(sweep8, f, p, "gap_mean")) == pytest.approx(x, abs=0.51), (p, f)


def test_collapse_without_pads_is_total(sweep8):
    zero = [r for r in sweep8 if r["p"] == 0]
    assert len(zero) == 120 and all(r["spread_q"] == pytest.approx(0.0, abs=1e-12) and r["overlap_q"] == 7 for r in zero)


def test_pad_weight_and_reweighting_n8(small8):
    frows, r4, r8 = small8
    assert len(frows) == 240 and len(r4) == 360 and len(r8) == 360
    for f, gap, sp in ((0.25, 15.4, 0.10), (1.0, 8.6, 0.31), (4.0, 6.4, 0.75), (16.0, 6.2, 1.28)):
        rs = [r for r in frows if r["factor"] == f]
        assert len(rs) == 60 and pc(ev.median_of(rs, "gap_q")) == pytest.approx(gap, abs=0.051) and ev.median_of(rs, "spread_q") == pytest.approx(sp, abs=0.006), f
    exp4 = {0: (8.6, 0.31, 100.0), 1: (6.1, 0.12, 82.0), 2: (8.6, 0.08, 80.0), 5: (9.3, 0.07, 79.0), 10: (9.3, 0.07, 79.0), 20: (9.3, 0.07, 79.0)}
    exp8 = {0: (6.5, 0.41, 100.0), 1: (3.6, 0.23, 91.0), 2: (4.2, 0.17, 88.0), 5: (4.1, 0.12, 88.0), 10: (4.1, 0.11, 88.0), 20: (4.2, 0.11, 88.0)}
    for rows, exp in ((r4, exp4), (r8, exp8)):
        for k, (gap, sp, ln) in exp.items():
            rs = [r for r in rows if r["reweights"] == k]
            assert len(rs) == 60 and pc(ev.median_of(rs, "gap")) == pytest.approx(gap, abs=0.051) and ev.median_of(rs, "spread") == pytest.approx(sp, abs=0.006) and pc(ev.median_of(rs, "length")) == pytest.approx(ln, abs=0.51), k


def test_n12_beyond_enumeration(sweep12):
    assert len(sweep12) == 60 and not any(r["exact"] for r in sweep12)
    exp = {4: (10.4, 11.4, 0, 0, 10, 17, 10.0, 0.20, 0.03), 8: (8.8, 7.0, 0, 1, 19, 10, 9.0, 0.27, 0.05)}
    for p, (gq, gb, hq, hb, better, worse, ov, sq, sb) in exp.items():
        sm = ev.pad_summary(sweep12, p)
        assert sm["count"] == 30 and pc(sm["gap_q"]) == pytest.approx(gq, abs=0.051) and pc(sm["gap_b"]) == pytest.approx(gb, abs=0.051) and (sm["hit_q"], sm["hit_b"], sm["b_better"], sm["b_worse"], sm["overlap_q"]) == (hq, hb, better, worse, ov)
        assert sm["spread_q"] == pytest.approx(sq, abs=0.006) and sm["spread_b"] == pytest.approx(sb, abs=0.006)
    q = {4: (25, 5, 8, 9, 13, 20), 8: (7, 4, 9, 6, 13, 22)}
    for p, vals in q.items():
        for f, x in zip(C.FAMILIES, vals):
            assert pc(ev.family_gap(sweep12, f, p)) == pytest.approx(x, abs=0.51), (p, f)
