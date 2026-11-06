"""Kennzahlen, Vergleiche über Instanzen und Verdikte. Jedes Verdikt ist eine reine Funktion (Art, Text); die App ruft st.<Art>(Text).

Alle Aussagen gelten für die gerechneten Instanzen, die sechs erfundenen Familien, die **erfundenen Pads** (Zahl, Ort, Gewicht, Verbindungen) und die **einfachen** Fassungen dieser Demo (quadratische Platzierung, Umgewichtung „Bound2Bound-artig“, Rundung durch Zuordnung); Zeiten stehen nie in Verdikten.
Die Lücke ist (Kosten − Vergleichswert) / Vergleichswert; der Vergleichswert ist bis n = 9 das aufgezählte Optimum, ab n = 12 die beste von 100 Abstiegen (die Lücke ist dann eine **obere** Grenze der wahren Lücke)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import qpl_constants as C
import qpl_place as Pl
from qpl_instance import hand_instance, make_instance


@dataclass(frozen=True)
class Settings:
    family: str = C.DEFAULT_FAMILY
    n: int = C.DEFAULT_N
    seed: int = C.DEFAULT_SEED
    pads: int = C.DEFAULT_PADS
    factor: float = C.DEFAULT_FACTOR
    reweights: int = C.DEFAULT_REWEIGHTS


# ----------------------------------------------------------------------------- Formatierung

def de(x: float, digits: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma und typografischem Minuszeichen."""
    return f"{x:.{digits}f}".replace(".", ",").replace("-", "−")


def pct(x: float, digits: int = 0) -> str:
    return de(100.0 * x, digits) + " %"


def fam(name: str) -> str:
    return C.FAMILY_NAMES.get(name, name)


def num(x: float) -> str:
    """Ganze Zahl ohne Nachkommastelle, sonst eine Stelle: 27 / 27,5 / −12,1."""
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else de(x, 1)


def rel(a: float, b: float) -> float:
    """(a − b) / b; NaN, wenn b = 0; Rundungsreste unter 1e-12 werden zu 0."""
    if not b:
        return float("nan")
    r = (a - b) / b
    return 0.0 if abs(r) < 1e-12 else r


def median_of(rows: list, key: str) -> float:
    return float(np.median([r[key] for r in rows]))


def padtext(p: int) -> str:
    return "ohne Pads" if p == 0 else (f"{p} Pads")


# ----------------------------------------------------------------------------- eine Instanz

def _result(inst, pads, c, X, ref) -> dict:
    perm = Pl.round_to_slots(inst, X)
    cost = Pl.cost_of(perm, inst.F, inst.D, c)
    return {"X": X, "perm": perm, "cost": cost, "gap": rel(cost, ref), "spread": Pl.spread(inst, X), "overlap": Pl.overlap(inst, X), "length": Pl.continuous_length(inst, X, pads), "qvalue": Pl.quadratic_value(inst, X, pads)}


def solve_instance(inst, p: int, seed: int, factor: float, reweights: int) -> dict:
    """Pads, Kosten, Vergleichswert, quadratische Lösung und umgewichtete Lösung (beide gerundet) für eine Instanz."""
    pads = Pl.make_pads(inst, p, seed, factor)
    c = Pl.linear_costs(inst, pads)
    ref, perm_ref, exact, mean = Pl.reference(inst, c, seed)
    q = _result(inst, pads, c, Pl.positions(inst, pads, 0), ref)
    b = _result(inst, pads, c, Pl.positions(inst, pads, reweights), ref)
    return {"inst": inst, "pads": pads, "c": c, "ref": ref, "ref_perm": perm_ref, "exact": exact, "mean": mean, "q": q, "b": b, "reweights": reweights}


def instance_data(s: Settings) -> dict:
    inst = make_instance(s.family, s.n, s.seed)
    v = solve_instance(inst, s.pads, s.seed, s.factor, s.reweights)
    v["gap_mean"] = rel(v["mean"], v["ref"]) if v["mean"] is not None else None
    return v


def pads_curve(s: Settings) -> list:
    """Für 0, 2, 4, 8 Pads (gleicher Seed, gleiches Gewicht): Streuung, Überlappung, Lücke der quadratischen Platzierung."""
    inst = make_instance(s.family, s.n, s.seed)
    out = []
    for p in C.PAD_CHOICES:
        v = solve_instance(inst, p, s.seed, s.factor, 0)
        out.append({"p": p, "spread": v["q"]["spread"], "overlap": v["q"]["overlap"], "gap": v["q"]["gap"], "ref": v["ref"]})
    return out


def factor_curve(s: Settings) -> list:
    """Für das Pad-Gewicht ×0,25 / ×1 / ×4 / ×16 (gleiche Pads): Streuung, Überlappung und Lücke der quadratischen Platzierung."""
    inst = make_instance(s.family, s.n, s.seed)
    out = []
    for f in C.FACTOR_CHOICES:
        v = solve_instance(inst, s.pads, s.seed, f, 0)
        out.append({"factor": f, "spread": v["q"]["spread"], "overlap": v["q"]["overlap"], "gap": v["q"]["gap"], "ref": v["ref"]})
    return out


def reweight_curve(s: Settings, v: dict) -> list:
    """Für 0, 1, 2, 5, 10, 20 Umgewichtungen (gleiche Pads, gleicher Vergleichswert): stetige Länge relativ zur quadratischen Lösung, Streuung, Überlappung, Lücke nach der Rundung."""
    inst, pads, c, ref = v["inst"], v["pads"], v["c"], v["ref"]
    steps = Pl.positions(inst, pads, max(C.REWEIGHT_CHOICES), trace=True)
    base = Pl.continuous_length(inst, steps[0], pads)
    out = []
    for r in C.REWEIGHT_CHOICES:
        res = _result(inst, pads, c, steps[r], ref)
        out.append({"reweights": r, "length": res["length"] / base if base else float("nan"), "spread": res["spread"], "overlap": res["overlap"], "gap": res["gap"]})
    return out


# ----------------------------------------------------------------------------- Zeilen für die Vergleiche

def row_of(family: str, n: int, seed: int, p: int, factor: float = 1.0, reweights: int = C.DEFAULT_REWEIGHTS) -> dict:
    inst = make_instance(family, n, seed)
    v = solve_instance(inst, p, seed, factor, reweights)
    q, b = v["q"], v["b"]
    return {"family": family, "n": n, "seed": seed, "p": p, "factor": factor, "ref": v["ref"], "exact": v["exact"], "gap_mean": rel(v["mean"], v["ref"]) if v["mean"] is not None else float("nan"),
            "gap_q": q["gap"], "gap_b": b["gap"], "hit_q": q["cost"] <= v["ref"] + 1e-9, "hit_b": b["cost"] <= v["ref"] + 1e-9, "spread_q": q["spread"], "spread_b": b["spread"], "overlap_q": q["overlap"],
            "overlap_b": b["overlap"], "length_ratio": q["length"] / b["length"] if b["length"] else float("nan"), "b_better": b["cost"] < q["cost"] - 1e-9, "b_worse": b["cost"] > q["cost"] + 1e-9,
            "q_below": q["cost"] < v["ref"] - 1e-9}


def sweep_pads(family: str, n: int, seeds, pads_list) -> list:
    return [row_of(family, n, s, p) for s in seeds for p in pads_list]


def sweep_factor(family: str, n: int, seeds, p: int = 4) -> list:
    return [row_of(family, n, s, p, f, 0) for s in seeds for f in C.FACTOR_CHOICES]


def sweep_reweights(family: str, n: int, seeds, p: int) -> list:
    """Je Instanz und Zahl der Umgewichtungen eine Zeile (gleicher Vergleichswert je Instanz)."""
    rows = []
    for s in seeds:
        inst = make_instance(family, n, s)
        v = solve_instance(inst, p, s, 1.0, 0)
        for r in _reweight_rows(v):
            rows.append(dict(r, family=family, n=n, seed=s, p=p))
    return rows


def _reweight_rows(v: dict) -> list:
    return reweight_curve(Settings(), v)


def pooled(by_family: dict) -> list:
    return [r for f in C.FAMILIES if f in by_family for r in by_family[f]]


def pad_summary(rows: list, p: int) -> dict:
    """Zusammenfassung der Zeilen mit `p` Pads (über alle übergebenen Familien)."""
    rs = [r for r in rows if r["p"] == p]
    return {"p": p, "count": len(rs), "gap_q": median_of(rs, "gap_q"), "gap_b": median_of(rs, "gap_b"), "gap_mean": median_of(rs, "gap_mean") if not np.isnan(rs[0]["gap_mean"]) else float("nan"),
            "hit_q": sum(r["hit_q"] for r in rs), "hit_b": sum(r["hit_b"] for r in rs), "spread_q": median_of(rs, "spread_q"), "spread_b": median_of(rs, "spread_b"), "overlap_q": median_of(rs, "overlap_q"),
            "b_better": sum(r["b_better"] for r in rs), "b_worse": sum(r["b_worse"] for r in rs), "length_ratio": median_of(rs, "length_ratio")}


def family_gap(rows: list, family: str, p: int, key: str = "gap_q") -> float:
    return median_of([r for r in rows if r["family"] == family and r["p"] == p], key)


# ----------------------------------------------------------------------------- Verdikte

def _head(s: Settings, v: dict) -> str:
    inst = v["inst"]
    w = "" if s.pads == 0 else (f", Pad-Gewicht ×{de(s.factor, 2).rstrip('0').rstrip(',')}")
    return f"Familie **{fam(s.family)}**, {s.n} Bauteile, Raster {inst.rows}×{inst.cols}, Seed {s.seed}, {padtext(s.pads)}{w}"


def _refname(v: dict) -> str:
    return "das aufgezählte Optimum" if v["exact"] else "die beste von 100 Abstiegen (obere Grenze)"


def verdict_system(s: Settings, v: dict):
    """Quadratische Platzierung und Umgewichtung für die gewählte Instanz."""
    q, b = v["q"], v["b"]
    n = s.n
    if s.pads == 0:
        return "warning", (f"{_head(s, v)}: ohne Pads ist das System singulär, **alle {n} Bauteile liegen auf demselben Punkt** (Streuung {de(q['spread'], 2)}, {q['overlap']} von {n} Bauteilen teilen sich den nächsten Platz). "
                           f"Die Rundung ist beliebig: Kosten {num(q['cost'])} gegen {_refname(v)} {num(v['ref'])} (Lücke {pct(q['gap'], 1)}"
                           + (f"; die mittleren Kosten aller Anordnungen liegen {pct(v['gap_mean'], 1)} darüber" if v["mean"] is not None else "") + ").")
    kind = "success" if q["gap"] <= 0.10 else "info"
    return kind, (f"{_head(s, v)}: die quadratische Platzierung streut die Bauteile auf {de(q['spread'], 2)} der Streuung der Plätze, {q['overlap']} von {n} Bauteilen teilen sich den nächsten Platz. Nach der Rundung durch eine Zuordnung kostet die Anordnung "
                  f"**{num(q['cost'])}** gegen {_refname(v)} {num(v['ref'])} (Lücke **{pct(q['gap'], 1)}**"
                  + (f"; mittlere Kosten aller Anordnungen {pct(v['gap_mean'], 1)} über dem Optimum" if v["mean"] is not None else "") + f"). Nach {s.reweights} Umgewichtungen: Streuung {de(b['spread'], 2)}, stetige Länge {pct(b['length'] / q['length'])} der quadratischen Lösung, "
                  f"Kosten {num(b['cost'])} (Lücke {pct(b['gap'], 1)}).")


def verdict_collapse(s: Settings, curve: list):
    """Streuung und Lücke gegen die Zahl der Pads."""
    txt = "; ".join(f"{c['p']} Pads: Streuung {de(c['spread'], 2)}, Überlappung {c['overlap']}, Lücke {pct(c['gap'], 1)}" for c in curve)
    return "info", f"Gleiche Instanz, quadratische Platzierung: {txt}. Ohne Pads fallen alle Bauteile auf einen Punkt; mit Pads wächst die Streuung, die Lücke nach der Rundung sinkt in der Regel (eine Instanz, kein Befund über die Familie)."


def verdict_factor(s: Settings, curve: list):
    """Streuung und Lücke gegen das Gewicht der Pads."""
    txt = "; ".join(f"×{de(c['factor'], 2).rstrip('0').rstrip(',')}: Streuung {de(c['spread'], 2)}, Lücke {pct(c['gap'], 1)}" for c in curve)
    return "info", f"Gleiche Instanz mit {s.pads} Pads, Pad-Gewicht gegen das Grundgewicht: {txt}. Schwache Anker lassen die Bauteile in der Mitte klumpen, starke ziehen sie zu den Pads (Streuung über 1: breiter verteilt als die Plätze, meist weil Bauteile zu den Pads außerhalb des Rasters gezogen werden)."


def verdict_reweight(s: Settings, curve: list):
    """Umgewichtung: Länge, Streuung, Lücke gegen die Zahl der Schritte."""
    base, last = curve[0], curve[-1]
    best = min(curve, key=lambda c: c["gap"])
    txt = "; ".join(f"{c['reweights']}: Länge {pct(c['length'])}, Streuung {de(c['spread'], 2)}, Lücke {pct(c['gap'], 1)}" for c in curve)
    return "info", (f"Umgewichtungen (stetige Länge relativ zur quadratischen Lösung): {txt}. Die Länge sinkt auf {pct(last['length'])}, die Streuung von {de(base['spread'], 2)} auf {de(last['spread'], 2)}; die kleinste Lücke nach der Rundung gibt es bei {best['reweights']} Umgewichtungen ({pct(best['gap'], 1)})."
                    if s.pads else "Ohne Pads ändert die Umgewichtung nichts: alle Bauteile liegen auf demselben Punkt.")


def verdict_sweep_pads(n: int, rows: list):
    """Vergleich über feste Instanzen: Lücke je Zahl der Pads."""
    ps = sorted({r["p"] for r in rows})
    sums = {p: pad_summary(rows, p) for p in ps}
    exact = rows[0]["exact"]
    txt = "; ".join(f"{p} Pads: {pct(sums[p]['gap_q'], 1)}" + (f" (Zufall {pct(sums[p]['gap_mean'], 0)})" if exact else "") for p in ps)
    nb = "; ".join(f"{p} Pads: besser in {sums[p]['b_better']}, schlechter in {sums[p]['b_worse']} von {sums[p]['count']}" for p in ps if p)
    return "info", (f"Bei n = {n}, Median der Lücke der quadratischen Platzierung über {sums[ps[0]]['count']} Instanzen je Zahl der Pads: {txt}. Die Umgewichtung ({C.DEFAULT_REWEIGHTS} Schritte) ist gegenüber der quadratischen Platzierung nach der Rundung {nb}; "
                    f"das Optimum treffen quadratisch {', '.join(str(sums[p]['hit_q']) for p in ps)} und umgewichtet {', '.join(str(sums[p]['hit_b']) for p in ps)} Instanzen ({', '.join(str(p) for p in ps)} Pads)."
                    + ("" if exact else " Der Vergleichswert ist die beste von 100 Abstiegen: obere Grenze der Lücke."))


def verdict_sweep_factor(rows: list):
    fs = sorted({r["factor"] for r in rows})
    txt = "; ".join(f"×{de(f, 2).rstrip('0').rstrip(',')}: Lücke {pct(median_of([r for r in rows if r['factor'] == f], 'gap_q'), 1)}, Streuung {de(median_of([r for r in rows if r['factor'] == f], 'spread_q'), 2)}" for f in fs)
    return "info", f"Pad-Gewicht gegen das Grundgewicht, {len({(r['family'], r['seed']) for r in rows})} Instanzen mit 4 Pads, Median: {txt}."


def verdict_sweep_reweights(rows: list):
    rs = sorted({r["reweights"] for r in rows})
    txt = "; ".join(f"{k}: Lücke {pct(median_of([r for r in rows if r['reweights'] == k], 'gap'), 1)}, Streuung {de(median_of([r for r in rows if r['reweights'] == k], 'spread'), 2)}, Länge {pct(median_of([r for r in rows if r['reweights'] == k], 'length'))}" for k in rs)
    return "info", f"Zahl der Umgewichtungen, {len({(r['family'], r['seed']) for r in rows})} Instanzen, Median: {txt}."


def verdict_core(s: Settings, v: dict):
    q = v["q"]
    return "info", (f"Die quadratische Platzierung löst bei {_head(s, v)} ein lineares System je Achse und rundet durch eine Zuordnung: Lücke {pct(q['gap'], 1)} gegen {_refname(v)}, Streuung {de(q['spread'], 2)}, Überlappung {q['overlap']} von {s.n}. "
                    + ("Hier gibt es keine Pads: alles liegt auf einem Punkt. " if s.pads == 0 else "Ohne Pads wäre es ein Punkt. ") + "Wie stark die Pads sein müssen, ob die Umgewichtung etwas bringt und wie es bei vielen Instanzen aussieht: Experiment 1 bis 5.")


# ----------------------------------------------------------------------------- Handbeispiel

def hand_data() -> dict:
    """Drei Bauteile auf einer Zeile, Fluss A–B 5, B–C 1; Pads bei x = −1 (an A) und x = 3 (an C) mit Gewicht 2: die Lösung von Hand und die Rundung."""
    inst = hand_instance()
    w = np.zeros((3, 2))
    w[0, 0] = w[2, 1] = 2.0
    pads = Pl.Pads(np.array([[-1.0, 0.0], [3.0, 0.0]]), w, 2.0, 1.0)
    c = Pl.linear_costs(inst, pads)
    X = Pl.positions(inst, pads)
    perm = Pl.round_to_slots(inst, X)
    return {"inst": inst, "pads": pads, "x": [float(x) for x in X[:, 0]], "perm": perm, "cost": Pl.cost_of(perm, inst.F, inst.D, c), "opt": float(Pl.all_costs(inst, c)[1].min())}
