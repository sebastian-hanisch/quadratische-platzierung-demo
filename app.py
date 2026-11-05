"""Quadratische Platzierung - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 9 der Reihe „Anordnen: relaxieren und runden“: die Orte der Bauteile werden reell relaxiert. Mit festen Pads (Ankern) ist das ein lineares Gleichungssystem; ohne Anker fällt alles auf einen Punkt. Danach rundet eine Zuordnung auf die Plätze,
und die Umgewichtung („Bound2Bound-artig“) kürzt die Länge, ohne die gerundete Anordnung zuverlässig zu verbessern. Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import qpl_constants as C
import qpl_place as Pl
from qpl_evaluation import (
    Settings,
    de,
    fam,
    factor_curve,
    hand_data,
    instance_data,
    median_of,
    num,
    pad_summary,
    pads_curve,
    padtext,
    pct,
    pooled,
    reweight_curve,
    sweep_factor,
    sweep_pads,
    sweep_reweights,
    verdict_collapse,
    verdict_core,
    verdict_factor,
    verdict_reweight,
    verdict_sweep_factor,
    verdict_sweep_pads,
    verdict_sweep_reweights,
    verdict_system,
)
from qpl_layout import dunkles_design, kopf_css
from qpl_pdf_export import build_pdf
from qpl_presets import bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sidebar_presets, sync_query_params
from qpl_visualization import build_arrangement, build_factor_curve, build_gap_bars, build_method_bars, build_pads_curve, build_positions, build_reweight_curve, build_spread_scatter

st.set_page_config(page_title="Quadratische Platzierung – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="Rechne die Platzierung …")
def _instance(settings: Settings):
    return instance_data(settings)


@st.cache_data(show_spinner=False)
def _pads_curve(settings: Settings):
    return pads_curve(settings)


@st.cache_data(show_spinner=False)
def _factor_curve(settings: Settings):
    return factor_curve(settings)


@st.cache_data(show_spinner=False)
def _reweight_curve(settings: Settings):
    return reweight_curve(settings, _instance(settings))


@st.cache_data(show_spinner=False)
def _sweep_pads(family, n, seeds, pads_list):
    return sweep_pads(family, n, seeds, pads_list)


@st.cache_data(show_spinner=False)
def _sweep_small(family, n):
    """Pad-Gewicht und Zahl der Umgewichtungen bei vier Pads: je Familie zehn feste Instanzen."""
    return sweep_factor(family, n, C.SWEEP_SEEDS_SMALL), sweep_reweights(family, n, C.SWEEP_SEEDS_SMALL, 4)


def verdict(pair):
    kind, text = pair
    getattr(st, kind)(text)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in qpl_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("📍 Quadratische Platzierung")
st.markdown(
    """
**Was passiert, wenn man die Orte reell relaxiert?** Dieselbe Aufgabe wie in Stück 1 bis 8: `n` Bauteile auf `n` Plätze, Kosten gleich der Summe aus **Fluss mal Abstand** über alle Paare, dazu **feste Pads** (Anker) um das Raster, an denen einzelne Bauteile hängen. Hier dürfen die Bauteile an **beliebigen Punkten**
der Ebene sitzen. Minimiert man die Summe der **Abstandsquadrate**, ist das ein **lineares Gleichungssystem** je Achse (Laplace-Matrix des Flussgraphen plus die Gewichte der Pads). **Ohne Anker fällt alles auf einen Punkt**; mit Ankern liegen die Bauteile verteilt, aber klumpig und auf stetigen Orten.
Eine **lineare Zuordnung** rundet auf die Plätze. Die **Umgewichtung** („Bound2Bound-artig“) rechnet das System mit Gewichten `F / |Δ|` mehrfach neu und minimiert so die lineare Länge.
Die sechs Familien der Flussmatrix sind **eigene, einfache Erfindungen** (aus Stück 2), die **Pads ebenso**; die Umgewichtung ist eine **eigene einfache Fassung**, nicht Bound2Bound der Literatur. Stück 9 der Reihe „Anordnen: relaxieren und runden“.

Weiter unten: **fünf Experimente** (**🔬**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert es", expanded=True):
    st.markdown(
        """
1. **Anker:** `p` feste Pads liegen auf einem Ring um das Raster; jedes hängt mit einem Gewicht an zwei zufälligen Bauteilen (Grundgewicht: der Median der positiven Flüsse).
2. **Das System:** je Achse `(L + diag(W)) x = b` mit der Laplace-Matrix `L = diag(Σ F) − F`, den Pad-Gewichten `W` je Bauteil und `b = Σ Gewicht · Pad-Lage`. Ohne Pads ist es singulär: alle Bauteile liegen auf demselben Punkt (hier hält ein schwacher Anker in der Mitte das System lösbar).
3. **Rundung:** die Zuordnung, die die Summe der Abstandsquadrate zwischen stetigem Ort und Platz minimiert. Die **Überlappung** zählt, wie viele Bauteile mit einem anderen denselben nächsten Platz haben: das muss die Zuordnung auflösen.
4. **Umgewichtung:** je Achse `F / max(|Δ|, 0,3)` statt `F`, einige Male neu gerechnet: die lineare (Manhattan-)Länge sinkt, die Bauteile rücken zusammen.
5. **Die Lücke:** (Kosten − Vergleichswert) / Vergleichswert. Bis n = 9 ist der Vergleichswert das aufgezählte Optimum, ab n = 12 die beste von 100 steilsten Abstiegen (obere Grenze der Lücke). Die quadratische Zielfunktion ist **keine Schranke** der Kosten.
6. **Feste Instanzen:** Vergleiche laufen über feste Seeds (n = 8: 20 Instanzen je Familie, n = 12: 5), nie über einen einzelnen.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Die Instanz**")
    family = st.selectbox("Familie der Flussmatrix", C.FAMILIES, key="family_select", format_func=lambda f: C.FAMILY_NAMES[f], help="Wie der Fluss zwischen den Bauteilen verteilt ist. Die Beschreibung steht unter dem Regler.")
    st.caption(C.FAMILY_HELP[family])
    n = st.select_slider("Bauteile n", options=C.SIZES, key="n_select", help="Bis n = 9 wird alles aufgezählt (Vergleichswert: Optimum); ab n = 12 steht die beste von 100 steilsten Abstiegen an seiner Stelle.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz", width="stretch", on_click=randomize_seed)
    st.markdown("**Die Anker**")
    pads_n = st.select_slider("Zahl der Pads", options=C.PAD_CHOICES, key="pads_select", help="Feste Anker auf dem Ring um das Raster; ohne Pads fällt alles auf einen Punkt.")
    factor = st.select_slider("Pad-Gewicht (Faktor)", options=C.FACTOR_CHOICES, key="factor_select", format_func=lambda f: f"×{f:g}", help="Faktor auf das Grundgewicht (Median der positiven Flüsse): schwache Anker lassen die Bauteile in der Mitte klumpen.")
    reweights = st.select_slider("Umgewichtungen", options=C.REWEIGHT_CHOICES, key="reweights_select", help="Wie oft das System mit Gewichten F / |Δ| neu gerechnet wird („Bound2Bound-artig“).")

sync_query_params({"family_select": family, "n_select": int(n), "seed_input": int(seed), "pads_select": int(pads_n), "factor_select": float(factor), "reweights_select": int(reweights)})
settings = Settings(family, int(n), int(seed), int(pads_n), float(factor), int(reweights))

v = _instance(settings)
q, b = v["q"], v["b"]
ref_label = "Optimum" if v["exact"] else "Beste gefundene Lösung"

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
m1, m2, m3 = st.columns(3)
m4, m5 = st.columns(2)
m1.metric("Lücke, quadratisch", pct(q["gap"], 1), delta=f"Kosten {num(q['cost'])}", delta_color="off", help="Kosten der Anordnung nach der Rundung der quadratischen Platzierung, gegen den Vergleichswert.")
m2.metric(f"Lücke, {settings.reweights} Umgewichtungen", pct(b["gap"], 1), delta=f"Kosten {num(b['cost'])}", delta_color="off", help="Dasselbe nach den Umgewichtungen („Bound2Bound-artig“).")
m3.metric("Streuung der stetigen Orte", de(q["spread"], 2), delta=f"Überlappung {q['overlap']} von {settings.n}", delta_color="off", help="Streuung im Verhältnis zur Streuung der Plätze (0 = ein Punkt); Überlappung: Bauteile mit demselben nächsten Platz wie ein anderes.")
m4.metric(ref_label, num(v["ref"]), help="Die kleinsten Kosten aller n! Anordnungen (aufgezählt)." if v["exact"] else "Die beste von 100 steilsten Abstiegen aus Zufallsstarts: eine obere Schranke des Optimums.")
m5.metric("Pads", padtext(settings.pads), delta=(f"Gewicht ×{settings.factor:g}" if settings.pads else None), delta_color="off")
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(build_positions(v["inst"], v["pads"], q["X"], q["perm"], "Quadratische Platzierung und Rundung"), width="stretch", key="positions_q")
with c2:
    st.plotly_chart(build_positions(v["inst"], v["pads"], b["X"], b["perm"], f"Nach {settings.reweights} Umgewichtungen"), width="stretch", key="positions_b")

if st.button("📄 PDF des aktuellen Ergebnisses erstellen", key="pdf_make"):
    st.session_state["pdf_made"] = (settings, build_pdf(settings, v))
made = st.session_state.get("pdf_made")
if made and made[0] == settings:
    st.download_button("⬇️ PDF herunterladen", data=made[1], file_name="quadratische-platzierung.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Was passiert, wenn man die Orte reell relaxiert?")
verdict(verdict_core(settings, v))

st.markdown("---")

# --- Experiment 1 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Ohne Anker fällt alles zusammen")
st.caption("Dieselbe Instanz mit 0, 2, 4 und 8 Pads: die Streuung der stetigen Orte (Balken) und die Lücke nach der Rundung (Linie). Der Vergleichswert wird für jede Zahl von Pads neu bestimmt, denn die Pads gehören zu den Kosten.")
pc = _pads_curve(settings)
st.plotly_chart(build_pads_curve(pc), width="stretch", key="pads_curve")
verdict(verdict_collapse(settings, pc))
verdict(verdict_system(settings, v))

st.markdown("---")

# --- Experiment 2 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Das lineare System und das Gewicht der Anker")
st.caption("Die Matrix des Systems (Laplace-Matrix des Flussgraphen plus Pad-Gewichte auf der Diagonale) und, rechts, die Wirkung des Pad-Gewichts: schwache Anker lassen die Bauteile in der Mitte klumpen.")
e1, e2 = st.columns(2)
with e1:
    mat = Pl.system_matrix(v["inst"], v["pads"])
    st.dataframe(pd.DataFrame(mat, index=list(v["inst"].names), columns=list(v["inst"].names)).round(1), width="stretch")
    st.caption("Zeilensumme = Summe der Pad-Gewichte des Bauteils; ohne Pads ist jede Zeilensumme 0 (das System ist singulär).")
with e2:
    if settings.pads:
        fc = _factor_curve(settings)
        st.plotly_chart(build_factor_curve(fc), width="stretch", key="factor_curve")
    else:
        st.info("Ohne Pads gibt es kein Pad-Gewicht: Pads einstellen (Seitenleiste).")
if settings.pads:
    verdict(verdict_factor(settings, fc))
with st.expander("Handbeispiel zum Nachrechnen"):
    h = hand_data()
    st.markdown(
        f"**Drei Bauteile auf einer Zeile** (Plätze bei x = 0, 1, 2), Fluss A–B 5, B–C 1; ein Pad bei x = −1 hängt mit Gewicht 2 an A, ein Pad bei x = 3 mit Gewicht 2 an C. Die Gleichungen: `7·x_A = 5·x_B − 2`, `6·x_B = 5·x_A + x_C`, `3·x_C = x_B + 6`. Von Hand: `44·x_B = 12`, also "
        f"**x_A = −1/11 ≈ {de(h['x'][0], 3)}, x_B = 3/11 ≈ {de(h['x'][1], 3)}, x_C = 23/11 ≈ {de(h['x'][2], 3)}**. Die Rundung setzt A, B, C auf die Plätze {', '.join(str(p + 1) for p in h['perm'])}: Kosten **{num(h['cost'])}**, das Optimum ist {num(h['opt'])}."
    )

st.markdown("---")

# --- Experiment 3 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Die Rundung und der Vergleich über feste Instanzen")
st.caption("Links die Anordnung, die die Rundung der quadratischen Platzierung ergibt, rechts die beste bekannte Anordnung. Darunter, über feste Instanzen, die Lücke je Familie und Zahl der Pads.")
r1, r2 = st.columns(2)
with r1:
    st.plotly_chart(build_arrangement(v["inst"], q["perm"], f"Nach der Rundung (Kosten {num(q['cost'])})"), width="stretch", key="arrangement_q")
with r2:
    st.plotly_chart(build_arrangement(v["inst"], v["ref_perm"], f"{ref_label} (Kosten {num(v['ref'])})"), width="stretch", key="arrangement_ref")

st.markdown(f"**Vergleich über feste Instanzen** (n = {C.SWEEP_N}, je Familie {len(C.SWEEP_SEEDS)} Instanzen, 0, 2, 4 und 8 Pads, Optimum aufgezählt).")
if not st.session_state.get("sweep_ok"):
    st.info("Der Vergleich rechnet 6 Reihen zu je 20 Instanzen und vier Pad-Zahlen und dauert rund eine halbe Minute (auf Streamlit Cloud länger). Mit dem Knopf starten:")
    if st.button("⏱️ Vergleich rechnen (n = 8)", key="sweep_button"):
        bar = st.progress(0.0, text="Rechne die Familien …")
        for i, f in enumerate(C.FAMILIES):
            _sweep_pads(f, C.SWEEP_N, C.SWEEP_SEEDS, C.PAD_CHOICES)
            bar.progress((i + 1) / len(C.FAMILIES), text=f"{C.FAMILY_NAMES[f]} fertig")
        st.session_state["sweep_ok"] = True
        st.rerun()
else:
    by = {f: _sweep_pads(f, C.SWEEP_N, C.SWEEP_SEEDS, C.PAD_CHOICES) for f in C.FAMILIES}
    rows = pooled(by)
    st.plotly_chart(build_gap_bars(rows, median_of, f"Lücke nach der Rundung je Familie, n = {C.SWEEP_N}"), width="stretch", key="gap_chart")
    table = []
    for p in C.PAD_CHOICES:
        sm = pad_summary(rows, p)
        table.append({"Pads": p, "Lücke quadratisch (Median)": pct(sm["gap_q"], 1), "Lücke umgewichtet (Median)": pct(sm["gap_b"], 1), "Zufall (mittlere Kosten)": pct(sm["gap_mean"]), "Optimum getroffen (q / u)": f"{sm['hit_q']} / {sm['hit_b']} von {sm['count']}",
                      "Streuung (q / u)": f"{de(sm['spread_q'], 2)} / {de(sm['spread_b'], 2)}", "Überlappung (q)": num(sm["overlap_q"])})
    st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
    st.plotly_chart(build_spread_scatter(rows, f"Streuung gegen Lücke, n = {C.SWEEP_N}"), width="stretch", key="scatter_chart")
    verdict(verdict_sweep_pads(C.SWEEP_N, rows))

st.markdown("---")

# --- Experiment 4 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Umgewichtung („Bound2Bound-artig“)")
st.caption("Nach jeder Umgewichtung: die stetige Länge (relativ zur quadratischen Lösung), die Streuung und die Lücke nach der Rundung für die gewählte Instanz. Darunter dasselbe über feste Instanzen und das Pad-Gewicht.")
rc = _reweight_curve(settings)
st.plotly_chart(build_reweight_curve(rc), width="stretch", key="reweight_curve")
verdict(verdict_reweight(settings, rc))
if not st.session_state.get("small_ok"):
    st.info("Der Vergleich über feste Instanzen (n = 8, vier Pads, je Familie zehn Instanzen, Pad-Gewicht und Umgewichtungen) dauert rund eine halbe Minute (auf Streamlit Cloud länger). Mit dem Knopf starten:")
    if st.button("⏱️ Pad-Gewicht und Umgewichtungen rechnen (n = 8)", key="small_button"):
        bar = st.progress(0.0, text="Rechne die Familien …")
        for i, f in enumerate(C.FAMILIES):
            _sweep_small(f, C.SWEEP_N)
            bar.progress((i + 1) / len(C.FAMILIES), text=f"{C.FAMILY_NAMES[f]} fertig")
        st.session_state["small_ok"] = True
        st.rerun()
else:
    parts = [_sweep_small(f, C.SWEEP_N) for f in C.FAMILIES]
    frows = [r for fr, _ in parts for r in fr]
    rrows = [r for _, rr in parts for r in rr]
    verdict(verdict_sweep_factor(frows))
    verdict(verdict_sweep_reweights(rrows))

st.markdown("---")

# --- Experiment 5: große Instanzen --------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Jenseits der Aufzählung")
st.caption(f"Für n = {C.LARGE_SWEEP_N}: die quadratische Platzierung und die Umgewichtung gegen die beste von {C.STARTS} steilsten Abstiegen (obere Grenze der Lücke), je Familie {len(C.LARGE_SEEDS)} feste Instanzen, vier und acht Pads.")
if not st.session_state.get("large_ok"):
    st.info("Die Rechnung dauert rund eine Minute (auf Streamlit Cloud länger). Mit dem Knopf starten:")
    if st.button(f"⏱️ Große Instanzen rechnen (n = {C.LARGE_SWEEP_N})", key="large_button"):
        bar = st.progress(0.0, text="Rechne die Familien …")
        for i, f in enumerate(C.FAMILIES):
            _sweep_pads(f, C.LARGE_SWEEP_N, C.LARGE_SEEDS, (4, 8))
            bar.progress((i + 1) / len(C.FAMILIES), text=f"{C.FAMILY_NAMES[f]} fertig")
        st.session_state["large_ok"] = True
        st.rerun()
else:
    by_big = {f: _sweep_pads(f, C.LARGE_SWEEP_N, C.LARGE_SEEDS, (4, 8)) for f in C.FAMILIES}
    rows_big = pooled(by_big)
    st.plotly_chart(build_method_bars(rows_big, median_of, f"Quadratisch und umgewichtet, n = {C.LARGE_SWEEP_N}"), width="stretch", key="large_chart")
    table = []
    for p in (4, 8):
        sm = pad_summary(rows_big, p)
        table.append({"Pads": p, "Lücke quadratisch (Median)": pct(sm["gap_q"], 1), "Lücke umgewichtet (Median)": pct(sm["gap_b"], 1), "Überlappung (Median)": num(sm["overlap_q"]), "Streuung (q / u)": f"{de(sm['spread_q'], 2)} / {de(sm['spread_b'], 2)}"})
    st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
    verdict(verdict_sweep_pads(C.LARGE_SWEEP_N, rows_big))

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Pads sind erfunden** | Zahl, Ort, Gewicht und Verbindungen der Pads sind eigene Erfindungen; eine andere Ankeranordnung kann die Lücken ändern. Aussagen gelten für diese Anker. | – |
| **Die sechs Familien sind erfunden** | Echte Platinen haben andere Strukturen; „dünn besetzte Flüsse zerfallen in Teile ohne Anker“ gilt nur für diese Familien. | – |
| **Die Rundung ist die einfachste Legalisierung** | Eine Zuordnung löst die Überlappung auf, ohne die Dichte zu beachten; die Look-ahead-Legalisierung und die Detailplatzierung sind hier nicht gebaut. | Stück 10, Stück 12 |
| **Die Umgewichtung ist „Bound2Bound-artig“** | Sie kennt nur 2-Pin-Verbindungen und kein Netz mit Pins an den Rändern; Bound2Bound der Literatur ist nicht gebaut und nicht nachgelesen. | – |
| **Keine Schranke** | Die quadratische Zielfunktion ist keine untere Schranke der Manhattan-Kosten; die Lücke misst gegen das Optimum oder die beste gefundene Lösung, nie gegen einen Beweis. | Stück 3 bis 8 |
| **Vergleichswert ab n = 12** | Die beste von 100 Abstiegen ist eine obere Grenze des Optimums, die Lücke eine obere Grenze der wahren Lücke. | – |
| **Wenige Instanzen** | n = 8: 20 Instanzen je Familie (Pad-Gewicht und Umgewichtungen: 10), n = 12: 5; kleine Unterschiede sind nicht belastbar. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Die Aufgabe (wie in Stück 1 und 8).** Symmetrischer Fluss $F$, Plätze $s_1, \dots, s_n$ im Raster, Pads $a_1, \dots, a_p$ mit Gewichten $w_{ij} \ge 0$ (Bauteil $i$ am Pad $j$); für die Anordnung $\pi$ ($\pi_i$ = Platz des Bauteils $i$) sind die Kosten
$$\mathrm{cost}(\pi) = \sum_{i<k} F_{ik}\, \lVert s_{\pi_i} - s_{\pi_k} \rVert_1 + \sum_{i,j} w_{ij}\, \lVert s_{\pi_i} - a_j \rVert_1 .$$

**Relaxation der Orte.** Die Bauteile dürfen an beliebigen Punkten $x_i \in \mathbb{R}^2$ sitzen. Man minimiert (je Achse, die Achsen sind unabhängig)
$$f(x) = \sum_{i<k} F_{ik}(x_i - x_k)^2 + \sum_{i,j} w_{ij}(x_i - a_j)^2 .$$
Der Gradient ist $2\big((L + W)x - b\big)$ mit der Laplace-Matrix $L = \mathrm{diag}(F\mathbf{1}) - F$, $W = \mathrm{diag}(w\mathbf{1})$ und $b_i = \sum_j w_{ij} a_j$; also löst man das **lineare System** $(L + W)\,x = b$. $L$ ist positiv semidefinit mit $L\mathbf{1} = 0$:
ohne Pads ($W = 0$) ist jedes $x = c\,\mathbf{1}$ ein Minimum, **alle Bauteile fallen auf einen Punkt**; $L + W$ ist genau dann regulär, wenn jede Zusammenhangskomponente des Flussgraphen mindestens ein Bauteil mit Pad-Gewicht enthält (sonst fällt diese Komponente zusammen; hier hält ein Anker $10^{-6}$ in der Mitte das System lösbar).

**Umgewichtung.** Für zwei Bauteile gilt $(x_i - x_k)^2 = |x_i - x_k| \cdot |x_i - x_k|$: gewichtet man die Verbindung mit $1 / \max(|x_i - x_k|, \varepsilon)$, ist der quadratische Wert gleich dem linearen $|x_i - x_k|$. Wiederholtes Neurechnen (iterativ umgewichtete kleinste Quadrate) minimiert die lineare Länge; $\varepsilon = 0{,}3$ Platzabstände.
Das ist der Grundgedanke von Bound2Bound für 2-Pin-Verbindungen; die Fassung hier ist **eigen**.

**Rundung.** Die Zuordnung $\pi$, die $\sum_i \lVert x_i - s_{\pi_i} \rVert_2^2$ minimiert (lineare Zuordnung, Ungarische Methode); Gleichstände werden nach Rundung der Abstandsquadrate auf acht Stellen entschieden, damit sie auf jedem Rechner gleich ausfallen.

**Streuung, Überlappung.** Streuung = Summe der Standardabweichungen der Orte je Achse, geteilt durch dieselbe Summe für die Plätze; Überlappung = $n$ minus Zahl der verschiedenen nächsten Plätze.

**Lücke.** $(\mathrm{cost} - U)/U$ mit dem Vergleichswert $U$ (aufgezähltes Optimum bis $n = 9$, sonst die beste von 100 steilsten Abstiegen mit Zusatzterm: eine **obere** Grenze des Optimums, die Lücke ist dann eine obere Grenze der wahren Lücke).

**Literatur.** Quadratische Platzierung und Bound2Bound-Netzmodell (Kraftwerk, Kraftwerk2, SimPL: Kim, Lee, Markov): Angaben aus der Fachliteratur übernommen, hier **nicht nachgelesen**; Selbstangaben der Autoren zur Güte werden nicht übernommen.
Das Gleichungssystem, der Kollaps ohne Anker, die Umgewichtung und die Rundung sind **eigene** Herleitungen und werden durch Tests (Handrechnung, Aufzählung, `scipy`) geprüft. Die Zahlen dieser Demo sind eigene Rechnungen an eigenen, erfundenen Familien und Pads.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
