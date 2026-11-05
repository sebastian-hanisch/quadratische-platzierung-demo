"""Plotly-Abbildungen. Alle 2D-Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import qpl_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380, legend_below=True):
    legend = dict(orientation="h", yanchor="top", y=-0.22, x=0) if legend_below else dict(orientation="h", yanchor="bottom", y=1.02, x=0)
    fig.update_layout(height=height + (40 if legend_below else 0), margin=dict(l=10, r=10, t=50, b=10), legend=legend, plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _extent(inst, pads, X):
    xs = [float(x) for x in inst.xy[:, 0]] + [float(x) for x in pads.pos[:, 0]] + [float(x) for x in X[:, 0]]
    ys = [-float(y) for y in inst.xy[:, 1]] + [-float(y) for y in pads.pos[:, 1]] + [-float(y) for y in X[:, 1]]
    return min(xs) - 0.6, max(xs) + 0.6, min(ys) - 0.6, max(ys) + 0.6


def build_positions(inst, pads, X, perm, title: str) -> go.Figure:
    """Plätze (graue Quadrate), Pads (Rauten) mit ihren Verbindungen, die stetigen Orte der Bauteile (Kreise) und, gestrichelt, der Platz, auf den die Rundung jedes Bauteil setzt."""
    fig = go.Figure()
    sx, sy = inst.xy[:, 0].astype(float), -inst.xy[:, 1].astype(float)
    fig.add_trace(go.Scatter(x=sx, y=sy, mode="markers", marker=dict(symbol="square", size=36, color="rgba(150,150,150,0.18)", line=dict(width=1, color="rgba(150,150,150,0.5)")), hoverinfo="skip", name="Plätze"))
    if pads.count:
        lx, ly = [], []
        for j in range(pads.count):
            for i in range(inst.n):
                if pads.w[i, j] > 0:
                    lx += [float(pads.pos[j, 0]), float(X[i, 0]), None]
                    ly += [-float(pads.pos[j, 1]), -float(X[i, 1]), None]
        fig.add_trace(go.Scatter(x=lx, y=ly, mode="lines", line=dict(width=1.2, color="rgba(176,138,46,0.5)"), hoverinfo="skip", name="Verbindung zum Pad"))
        fig.add_trace(go.Scatter(x=pads.pos[:, 0].astype(float), y=-pads.pos[:, 1].astype(float), mode="markers", marker=dict(symbol="diamond", size=14, color=C.COLORS["pad"]), name="Pads (fest)", hovertemplate="Pad<extra></extra>"))
    dx, dy = [], []
    for i in range(inst.n):
        dx += [float(X[i, 0]), float(sx[perm[i]]), None]
        dy += [-float(X[i, 1]), float(sy[perm[i]]), None]
    fig.add_trace(go.Scatter(x=dx, y=dy, mode="lines", line=dict(width=1, dash="dot", color="rgba(192,80,77,0.6)"), hoverinfo="skip", name="Rundung auf den Platz"))
    fig.add_trace(go.Scatter(x=X[:, 0].astype(float), y=-X[:, 1].astype(float), mode="markers+text", text=list(inst.names), textposition="top center", marker=dict(size=14, color=C.COLORS["cont"], line=dict(width=1, color="white")),
                             name="stetige Orte", hovertemplate="%{text}<extra></extra>"))
    x0, x1, y0, y1 = _extent(inst, pads, X)
    fig.update_layout(title=title)
    fig.update_xaxes(visible=False, range=[x0, x1], scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, range=[y0, y1])
    return _base(fig, height=360)


def build_arrangement(inst, perm, title: str) -> go.Figure:
    """Die gerundete Anordnung: Bauteile auf den Plätzen, Verbindungen mit Fluss als Linien."""
    fig = go.Figure()
    xs, ys = inst.xy[:, 0].astype(float), -inst.xy[:, 1].astype(float)
    pos = [(xs[int(perm[i])], ys[int(perm[i])]) for i in range(inst.n)]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", marker=dict(symbol="square", size=36, color="rgba(150,150,150,0.18)", line=dict(width=1, color="rgba(150,150,150,0.5)")), hoverinfo="skip", showlegend=False))
    fmax = max(1, int(inst.F.max()))
    lx, ly = [], []
    for a in range(inst.n):
        for b in range(a + 1, inst.n):
            if inst.F[a, b]:
                lx += [pos[a][0], pos[b][0], None]
                ly += [pos[a][1], pos[b][1], None]
    fig.add_trace(go.Scatter(x=lx, y=ly, mode="lines", line=dict(width=1.5, color="rgba(76,120,168,0.35)"), hoverinfo="skip", name="Fluss"))
    fig.add_trace(go.Scatter(x=[q[0] for q in pos], y=[q[1] for q in pos], mode="markers+text", text=list(inst.names), textposition="middle center", showlegend=False, marker=dict(size=26, color=C.COLORS["best"]), textfont=dict(color="white", size=10)))
    fig.update_layout(title=title)
    fig.update_xaxes(visible=False, range=[xs.min() - 0.7, xs.max() + 0.7], scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, range=[ys.min() - 0.7, ys.max() + 0.7])
    return _base(fig, height=300)


# ----------------------------------------------------------------------------- Kurven für die gewählte Instanz

def build_pads_curve(curve: list) -> go.Figure:
    """Streuung (Balken) und Lücke nach der Rundung (Linie) gegen die Zahl der Pads."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=[str(c["p"]) for c in curve], y=[c["spread"] for c in curve], name="Streuung der stetigen Orte", marker_color="rgba(76,120,168,0.7)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=[str(c["p"]) for c in curve], y=[100 * c["gap"] for c in curve], mode="lines+markers", name="Lücke nach der Rundung (%)", line=dict(color=C.COLORS["cont"], width=3)), secondary_y=True)
    fig.update_xaxes(title="Zahl der Pads")
    fig.update_yaxes(title="Streuung (1 = wie die Plätze)", secondary_y=False, fixedrange=True)
    fig.update_yaxes(title="Lücke (%)", secondary_y=True, fixedrange=True)
    fig.update_layout(title="Anker gegen Kollaps")
    return _base(fig, height=340)


def build_factor_curve(curve: list) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    xs = [f"×{c['factor']:g}" for c in curve]
    fig.add_trace(go.Bar(x=xs, y=[c["spread"] for c in curve], name="Streuung der stetigen Orte", marker_color="rgba(76,120,168,0.7)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=xs, y=[100 * c["gap"] for c in curve], mode="lines+markers", name="Lücke nach der Rundung (%)", line=dict(color=C.COLORS["cont"], width=3)), secondary_y=True)
    fig.update_xaxes(title="Pad-Gewicht gegen das Grundgewicht")
    fig.update_yaxes(title="Streuung (1 = wie die Plätze)", secondary_y=False, fixedrange=True)
    fig.update_yaxes(title="Lücke (%)", secondary_y=True, fixedrange=True)
    fig.update_layout(title="Gewicht der Anker")
    return _base(fig, height=340)


def build_reweight_curve(curve: list) -> go.Figure:
    """Stetige Länge (relativ), Streuung und Lücke nach der Rundung gegen die Zahl der Umgewichtungen."""
    fig = make_subplots(rows=1, cols=3, subplot_titles=("stetige Länge (relativ)", "Streuung", "Lücke nach der Rundung (%)"))
    xs = [str(c["reweights"]) for c in curve]
    fig.add_trace(go.Scatter(x=xs, y=[c["length"] for c in curve], mode="lines+markers", line=dict(color="#4c78a8", width=3), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=xs, y=[c["spread"] for c in curve], mode="lines+markers", line=dict(color="#2F6B65", width=3), showlegend=False), row=1, col=2)
    fig.add_trace(go.Scatter(x=xs, y=[100 * c["gap"] for c in curve], mode="lines+markers", line=dict(color=C.COLORS["cont"], width=3), showlegend=False), row=1, col=3)
    fig.update_xaxes(title="Umgewichtungen")
    return _base(fig, height=320, legend_below=False)


# ----------------------------------------------------------------------------- Vergleiche über feste Instanzen

def build_gap_bars(rows: list, median_of, title: str) -> go.Figure:
    """Median der Lücke nach der Rundung je Familie und Zahl der Pads (quadratische Platzierung)."""
    ps = sorted({r["p"] for r in rows})
    fams = [f for f in C.FAMILIES if any(r["family"] == f for r in rows)]
    fig = go.Figure()
    colors = {0: "#9aa0a6", 2: "#4c78a8", 4: "#2F6B65", 8: "#b08a2e"}
    for p in ps:
        fig.add_trace(go.Bar(x=[C.FAMILY_NAMES[f] for f in fams], y=[100 * median_of([r for r in rows if r["family"] == f and r["p"] == p], "gap_q") for f in fams], name=f"{p} Pads", marker_color=colors.get(p, "#8e6bb0")))
    fig.update_yaxes(title="Lücke nach der Rundung (%, Median)")
    fig.update_layout(title=title, barmode="group")
    return _base(fig, height=380)


def build_method_bars(rows: list, median_of, title: str) -> go.Figure:
    """Quadratisch gegen umgewichtet (Median der Lücke), dazu der Zufall (mittlere Kosten), je Zahl der Pads."""
    ps = sorted({r["p"] for r in rows})
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[str(p) for p in ps], y=[100 * median_of([r for r in rows if r["p"] == p], "gap_q") for p in ps], name="quadratisch", marker_color="#4c78a8"))
    fig.add_trace(go.Bar(x=[str(p) for p in ps], y=[100 * median_of([r for r in rows if r["p"] == p], "gap_b") for p in ps], name=f"umgewichtet ({C.DEFAULT_REWEIGHTS} Schritte)", marker_color="#2F6B65"))
    if rows[0]["exact"]:
        fig.add_trace(go.Scatter(x=[str(p) for p in ps], y=[100 * median_of([r for r in rows if r["p"] == p], "gap_mean") for p in ps], mode="lines+markers", name="Zufall (mittlere Kosten)", line=dict(color="rgba(150,150,150,0.9)", dash="dot", width=3)))
    fig.update_xaxes(title="Zahl der Pads")
    fig.update_yaxes(title="Lücke (%, Median)")
    fig.update_layout(title=title, barmode="group")
    return _base(fig, height=360)


def build_spread_scatter(rows: list, title: str) -> go.Figure:
    """Streuung gegen Lücke je Instanz (quadratisch), nach Zahl der Pads gefärbt."""
    fig = go.Figure()
    colors = {0: "#9aa0a6", 2: "#4c78a8", 4: "#2F6B65", 8: "#b08a2e"}
    for p in sorted({r["p"] for r in rows}):
        rs = [r for r in rows if r["p"] == p]
        fig.add_trace(go.Scatter(x=[r["spread_q"] for r in rs], y=[100 * r["gap_q"] for r in rs], mode="markers", name=f"{p} Pads", marker=dict(size=8, color=colors.get(p, "#8e6bb0")), hovertemplate="Streuung %{x:.2f}, Lücke %{y:.1f} %<extra></extra>"))
    fig.update_xaxes(title="Streuung der stetigen Orte")
    fig.update_yaxes(title="Lücke nach der Rundung (%)")
    fig.update_layout(title=title)
    return _base(fig, height=360)
