# Quadratische Platzierung – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-quadratische-platzierung-demo.streamlit.app/)** -->

Stück 9 von 15 der **Konzepte-Reihe „Anordnen: relaxieren und runden“** für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (die Konzepte-Seite der Reihe gibt es noch nicht). Die Stücke 3 bis 6 haben die **Zielfunktion** und die **Menge der Anordnungen** relaxiert ([Gilmore–Lawler](https://github.com/sebastian-hanisch/gilmore-lawler-demo), [doppeltstochastische Relaxation](https://github.com/sebastian-hanisch/birkhoff-relaxation-demo)), Stück 8, [Branch and Bound mit Schranke](https://github.com/sebastian-hanisch/schranke-im-baum-demo), hat den Beweis geführt. Dieses Stück relaxiert die **Orte** (Kante der Reihe: *Kontrast*): Statt auf den Plätzen eines Rasters dürfen die Bauteile an beliebigen Punkten der Ebene sitzen, und das Verfahren rundet danach auf die Plätze zurück.

## Warum dieses Problem

Minimiert man die Summe der **Abstandsquadrate** zwischen verbundenen Bauteilen, ist das kein kombinatorisches Problem mehr, sondern ein **lineares Gleichungssystem** je Achse (Laplace-Matrix des Flussgraphen plus die Gewichte **fester Pads**, der Anker). Das ist die Grundlage der analytischen Platzierung. Die Kernfrage: **Was passiert, wenn man die Orte reell relaxiert: was tun die Anker, wie gut ist die Anordnung nach der Rundung, und bringt die Umgewichtung („Bound2Bound-artig“) etwas?**

Die Antwort dieser Messung: **Ohne Anker fällt alles auf einen Punkt** (Streuung 0), die Rundung ist beliebig. Mit Ankern liegen die Bauteile verteilt, und eine Zuordnung rundet auf eine **brauchbare** Anordnung (Lücke im Median 6 bis 14 %, gegen 26 bis 38 % bei Zufall); das **Gewicht der Anker** entscheidet über die Streuung; die Umgewichtung kürzt die stetige Länge um ein Fünftel, lässt die Bauteile dabei zusammenrücken und verbessert die gerundete Anordnung im Median **nicht verlässlich**. Das sind **Befunde an sechs erfundenen Familien, erfundenen Pads und einfachen Eigenfassungen**, keine Sätze.

## Modell

- **Aufgabe** (wie in Stück 1 bis 8): `n` Bauteile auf `n` Plätze eines Rasters (Manhattan-Abstand), dazu `p` **feste Pads** auf einem Ring um das Raster; jedes Pad hängt mit einem Gewicht an zwei zufälligen Bauteilen (Grundgewicht: Median der positiven Flüsse, mindestens 1; Faktor wählbar). `cost(p) = Σ_{i<k} F[i,k] · |p_i − p_k|₁ + Σ_{i,Pad} w · |p_i − Pad|₁` (das QAP mit linearem Term, wie bei den Knoten in Stück 8). Kern (Kosten, Aufzählung, Zufall, sechs Familien der Flussmatrix, Ungarische Methode) als Kopie aus Stück 3 bis 8 (`qpl_cost.py`, `qpl_landscape.py`, `qpl_rng.py`, `qpl_instance.py`, `qpl_assignment.py`; Tests vergleichen die Instanzen mit den Schwester-Repos, wenn sie nebenan liegen). Die Familien und die Pads sind **eigene, einfache Erfindungen**, keine echten Platinen und keine QAPLIB-Instanzen.
- **Quadratische Platzierung** (`qpl_place.py`): minimiere je Achse `Σ_{i<k} F[i,k] (x_i − x_k)² + Σ w (x_i − a)²`. Das ergibt `(L + diag(W)) x = b` mit `L = diag(Σ_k F) − F`, den Pad-Gewichten `W` je Bauteil und `b = Σ w · a`. Ohne Pads ist `L` singulär (jeder gleiche Ort ist ein Minimum): **alle Bauteile fallen auf einen Punkt**; Bauteile ohne Weg zu einem Pad fallen ebenso; ein schwacher Anker `10⁻⁶` in der Mitte hält das System lösbar (`numpy.linalg.solve`).
- **Umgewichtung („Bound2Bound-artig“, eigene Fassung für 2-Pin-Verbindungen):** je Achse `F / max(|Δ|, 0,3)` statt `F` (ebenso für die Pads), mehrfach neu gerechnet: das minimiert die **lineare** Länge statt der quadratischen. Das ist **nicht** Bound2Bound der Literatur (Pins an den Rändern eines Netzes, Mehr-Pin-Netze), nur dessen Grundgedanke.
- **Rundung:** lineare Zuordnung (Ungarische Methode) der stetigen Orte auf die Plätze, kleinste Summe der Abstandsquadrate; die Quadrate werden vorher auf acht Stellen gerundet (`tie_quantized`), damit Gleichstände auf jedem Rechner gleich entschieden werden. Die **Überlappung** zählt, wie viele Bauteile mit einem anderen denselben nächsten Platz haben; die **Streuung** ist die Streuung der stetigen Orte im Verhältnis zur Streuung der Plätze (0 = ein Punkt).
- **Lücke und Vergleichswert:** `(Kosten − Vergleichswert) / Vergleichswert`; bis `n = 9` ist der Vergleichswert das aufgezählte Optimum (mit den Pads der Instanz), ab `n = 12` die beste von 100 steilsten Abstiegen (obere Grenze der Lücke). Die quadratische Zielfunktion ist **keine Schranke** der Kosten.
- **Experimente:** (1) ohne Anker: Kollaps, 0 / 2 / 4 / 8 Pads; (2) das lineare System und das Gewicht der Anker, Handbeispiel; (3) die Rundung und der Vergleich über feste Instanzen; (4) die Umgewichtung; (5) jenseits der Aufzählung (`n = 12`). Formeln im 📐-Expander der App.

## Methodik

Experiment 1, 2 und 4 rechnen **eine** Instanz (Pads, Pad-Gewicht und Zahl der Umgewichtungen sind Regler; `n` = 6, 8, 9 mit Aufzählung als Vergleichswert, `n` = 12, 16 mit der besten von 100 Abstiegen). Der Vergleich in Experiment 3 rechnet auf Knopfdruck je Familie 20 Instanzen bei `n = 8` (Seeds 100000 bis 100019) mit 0, 2, 4 und 8 Pads; Experiment 4 rechnet je Familie zehn Instanzen mit vier Pads (Pad-Gewicht ×0,25 / 1 / 4 / 16 und 0 / 1 / 2 / 5 / 10 / 20 Umgewichtungen); Experiment 5 rechnet je Familie fünf Instanzen bei `n = 12` mit vier und acht Pads. Der Vergleichswert hängt von den Pads ab (sie gehören zu den Kosten) und wird für jede Zahl von Pads neu bestimmt. Alle Aussagen laufen über feste Seeds, nie über einen einzelnen. Zeiten stehen nirgends als Zahl in Tests oder in dieser README.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` (Prozentwerte auf eine Stelle, die Werte je Familie auf ganze Prozent gerundet, Zählungen exakt). Reihenfolge der Familien: Netzliste, gleichverteilt, dünn besetzt, zwei Cluster, Stern, wenige starke Flüsse. **Die Rundung der quadratischen Platzierung ist in keinem der 480 Fälle (n = 8) billiger als das aufgezählte Optimum.**

| Frage | Befund |
|---|---|
| Handbeispiel | Drei Bauteile auf einer Zeile (Plätze bei 0, 1, 2; Fluss A–B 5, B–C 1); ein Pad bei −1 hängt mit Gewicht 2 an A, eines bei 3 mit Gewicht 2 an C. Die Gleichungen `7·x_A = 5·x_B − 2`, `6·x_B = 5·x_A + x_C`, `3·x_C = x_B + 6` ergeben **x_A = −1/11, x_B = 3/11, x_C = 23/11**; die Rundung setzt A, B, C auf die Plätze 1, 2, 3: Kosten **10**, das Optimum |
| Standardinstanz (Netzliste, n = 8, Seed 35, 4 Pads) | Optimum 50; quadratische Platzierung: Streuung **0,69**, **4 von 8** Bauteilen teilen sich den nächsten Platz, Rundung kostet **51 (Lücke 2,0 %)**; mittlere Kosten aller Anordnungen 52,0 % über dem Optimum. Nach 5 Umgewichtungen: stetige Länge 79,9 % der quadratischen Lösung, Streuung 0,33, Überlappung 5, Kosten 51 |
| Anker gegen Kollaps (dieselbe Instanz) | 0 / 2 / 4 / 8 Pads: Streuung 0,00 / 0,53 / 0,69 / 0,47, Überlappung 7 / 6 / 4 / 4, Lücke 58,1 / 4,4 / 2,0 / 2,3 % (Vergleichswert 31 / 45 / 50 / 88,5, er hängt an den Pads) |
| Gewicht der Anker (dieselbe Instanz, 4 Pads) | Faktor ×0,25 / ×1 / ×4 / ×16: Streuung 0,27 / 0,69 / 1,21 / 1,66, Lücke 9,5 / 2,0 / 1,0 / 0,3 %; über 1 liegt die Streuung, wenn die Bauteile zu den Pads außerhalb des Rasters gezogen werden |
| Ohne Anker, n = 8, 120 Instanzen | Streuung **0,00 in allen**, Überlappung 7 von 8; Lücke im Median **39,5 %** gegen Zufall (mittlere Kosten) 42,0 %; je Familie 44 / 19 / 94 / 41 / 19 / 89 % gegen Zufall 41 / 22 / 83 / 42 / 37 / 77 %: die Rundung ist beliebig |
| Mit Ankern, n = 8 (Median über 120 Instanzen) | **2 / 4 / 8 Pads: Lücke 14,1 / 9,3 / 6,2 %**, Zufall 38,1 / 34,5 / 26,1 %; Streuung 0,29 / 0,32 / 0,44; Überlappung 6 / 4 / 4; Optimum getroffen in 3 / 5 / 5 Instanzen |
| Lücke je Familie, n = 8 (quadratisch, in %) | 2 Pads: 15 / 7 / 21 / 15 / 12 / 32; 4 Pads: 11 / 6 / 9 / 7 / 12 / 14; 8 Pads: 7 / 4 / 4 / 6 / 7 / 10; Zufall bei 8 Pads: 25 / 20 / 26 / 26 / 27 / 43 |
| Gewicht der Anker, n = 8 (60 Instanzen, 4 Pads, Median) | Faktor ×0,25 / ×1 / ×4 / ×16: Lücke **15,4 / 8,6 / 6,4 / 6,2 %**, Streuung 0,10 / 0,31 / 0,75 / 1,28 |
| Umgewichtung, n = 8 (60 Instanzen je Pad-Zahl, Median) | **4 Pads**, 0 / 1 / 2 / 5 / 10 / 20 Umgewichtungen: stetige Länge 100 / 82 / 80 / 79 / 79 / 79 % der quadratischen, Streuung 0,31 / 0,12 / 0,08 / 0,07 / 0,07 / 0,07, Lücke 8,6 / 6,1 / 8,6 / 9,3 / 9,3 / 9,3 %; **8 Pads**: Länge 100 / 91 / 88 / 88 / 88 / 88 %, Streuung 0,41 / 0,23 / 0,17 / 0,12 / 0,11 / 0,11, Lücke 6,5 / 3,6 / 4,2 / 4,1 / 4,1 / 4,2 % |
| Quadratisch gegen umgewichtet (5 Umgewichtungen), n = 8, 120 Instanzen je Pad-Zahl | Lücke im Median 2 / 4 / 8 Pads: 14,1 / 9,3 / 6,2 % gegen **12,7 / 9,6 / 4,3 %**; umgewichtet besser in 43 / 44 / 61, schlechter in 38 / 50 / 41; Optimum getroffen in 4 / 4 / 14 gegen 3 / 5 / 5; stetige Länge der quadratischen Lösung im Median das 1,34- / 1,23- / 1,13-Fache der umgewichteten; Streuung umgewichtet 0,05 / 0,08 / 0,19. Je Familie bei 8 Pads: umgewichtet 6 / 3 / 3 / 1 / 7 / 6 %. **Keine klare Verbesserung** außer bei acht Pads |
| Jenseits der Aufzählung, n = 12 (5 Instanzen je Familie, Vergleichswert: beste von 100 Abstiegen) | 4 Pads: Lücke 10,4 % (quadratisch) gegen 11,4 % (umgewichtet), umgewichtet besser in 10, schlechter in 17 von 30; 8 Pads: **8,8 gegen 7,0 %**, besser in 19, schlechter in 10; Überlappung 10 / 9 von 12 Bauteilen; Streuung quadratisch 0,20 / 0,27, umgewichtet 0,03 / 0,05; Lücke je Familie quadratisch bei 4 Pads 25 / 5 / 8 / 9 / 13 / 20 %, bei 8 Pads 7 / 4 / 9 / 6 / 13 / 22 % (obere Grenzen der Lücke) |
| Orakel | Das System gleich `numpy.linalg.lstsq` und `scipy.linalg.solve`; die Lösung gleich dem Minimum, das ein allgemeiner Löser (BFGS) für dieselbe Zielfunktion findet; die Zuordnung der Rundung gleich `scipy.optimize.linear_sum_assignment` und der Aufzählung aller Zuordnungen; keine Rundung und keine beste gefundene Lösung ist billiger als das aufgezählte Optimum |

**Was die Zahlen nicht sagen:** Die Familien und die **Pads** (Zahl, Ort, Gewicht, Verbindungen) sind erfunden; eine andere Ankeranordnung kann die Lücken ändern. Die Rundung ist die einfachste Legalisierung: die Look-ahead-Legalisierung und die Detailplatzierung sind nicht gemessen. Bound2Bound der Literatur ist nicht gebaut; „Bound2Bound-artig“ ist die Umgewichtung für 2-Pin-Verbindungen. Ab `n = 12` sind die Lücken obere Grenzen; bei Experiment 4 sind es zehn Instanzen je Familie, bei `n = 12` fünf.

## Ehrliche Grenzen

- **Erfundene Pads:** Zahl, Ort, Gewicht und Verbindungen sind eigene Erfindungen; Befunde gelten für diese Anker.
- **Einfachste Rundung:** eine Zuordnung löst die Überlappung auf, ohne die Dichte zu beachten; Stück 10 (Look-ahead-Legalisierung) und Stück 12 (Detailplatzierung) setzen dort an.
- **Bound2Bound-artig, nicht Bound2Bound:** nur 2-Pin-Verbindungen, keine Netze mit Pins an den Rändern; die Aussage „die Umgewichtung verbessert die Rundung nicht verlässlich“ gilt für diese Fassung.
- **Keine Schranke:** die quadratische Zielfunktion ist keine untere Schranke der Manhattan-Kosten; gemessen wird gegen das Optimum oder die beste gefundene Lösung.
- **Erfundene Familien:** keine echten Platinen, keine QAPLIB-Instanzen; bei dünn besetzten Flüssen zerfällt der Flussgraph, Teile ohne Anker fallen in die Mitte.
- **Wenige Instanzen:** n = 8: 20 je Familie (Experiment 4: 10), n = 12: 5.
- **Rechnerabhängige Gleichstände:** die Rundung entscheidet Gleichstände (zusammenfallende Orte) nach acht Stellen Rundung; Änderungen dieser Festlegung ändern einzelne Zählungen („Optimum getroffen“).
- **Quellen:** Kraftwerk, Kraftwerk2 und SimPL (Kim, Lee, Markov) mit dem Bound2Bound-Netzmodell sind aus der Fachliteratur übernommen und **nicht nachgelesen**; das Gleichungssystem, der Kollaps ohne Anker, die Umgewichtung und die Rundung sind eigene Herleitungen und werden durch Tests (Handrechnung, Aufzählung, `scipy`) geprüft.

## Verifikation

- **Tests** (`pytest tests/`): **182 Tests**, rund zwei Minuten (Windows, Python 3.14). Handwerte (das Handbeispiel von Hand: `x = (−1/11, 3/11, 23/11)`, Kosten von Pads und Anordnungen), Eigenschaften (der Gradient des Systems ist null und die Lösung ein Minimum; ohne Pads fallen alle Bauteile auf einen Punkt; die Lösung verschiebt sich mit den Pads; schwächere Pads geben weniger Streuung; Teile ohne Weg zu einem Pad fallen in die Mitte; die Umgewichtung verkürzt die stetige Länge und erreicht einen Fixpunkt; die Rundung ist eine Anordnung und ändert sich bei Rechenrauschen von 1e-13 nicht; Abstieg und beste gefundene Lösung), Orakel (`lstsq`, `scipy.linalg.solve`, BFGS, `linear_sum_assignment`, Aufzählung; nur mit `requirements-dev.txt`), Randfälle (zwei Bauteile, Nullfluss, null Pads), Verdikte an handgesetzten Werten, Abbildungen, PDF, Rauchtest und Pfade der App (jede Familie, jede Pad-Zahl, `n` = 9, 12, 16, ohne Pads, alle drei Vergleiche), Layout, Footer und Laufzeit-Importe. `test_claims.py` rechnet jede Zahl dieser README nach.
- **Kopie:** Tests vergleichen die Familien mit denen von Stück 1 bis 8, sofern die Schwester-Repos nebenan liegen.
- **Nicht getestet:** Zeiten; kein Mutationstest; Linux-CI: noch nicht gelaufen (Repo noch nicht veröffentlicht).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: fünf Experimente, Vergleiche über feste Instanzen, Grenzen, Formulierung |
| `qpl_rng.py` | SplitMix64 (Kopie aus Stück 1) |
| `qpl_instance.py` | Instanzen: sechs Familien der Flussmatrix, Raster, Handbeispiele |
| `qpl_cost.py` | Kosten, Tausch-`Δ` (Kopie aus Stück 2) |
| `qpl_landscape.py` | Aufzählung für das Optimum (Kopie aus Stück 2) |
| `qpl_assignment.py` | Ungarische Methode (Kopie aus Stück 8) |
| `qpl_place.py` | Pads, lineares System, Umgewichtung, Rundung, Kosten mit linearem Term, Abstieg und beste gefundene Lösung |
| `qpl_evaluation.py` | Zeilen für die Vergleiche, Kurven, Zusammenfassungen, Verdikte |
| `qpl_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `qpl_pdf_export.py` | PDF-Export des Ergebnisses |
| `qpl_constants.py` | Größen, Familien, feste Reihen, Farben, Presets |
| `qpl_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Button |
| `qpl_layout.py` | Fester Kopf (Stylesheet) |
| `requirements-dev.txt` | Laufzeit plus pytest und scipy |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt; kein `scipy` zur Laufzeit) |
| `tests/` | Platzierung, Zuordnung, Kosten, Instanzen, Landschaft, Auswertung, Verdikte, Abbildungen, Presets, Layout, AppTest, Orakel, Zahlen der README, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Bound2Bound der Literatur (Mehr-Pin-Netze, Pins an den Rändern):** nur die Grundidee für 2-Pin-Verbindungen.
- **Look-ahead-Legalisierung (Stück 10), nichtlineare Dichte (Stück 11), Detailplatzierung (Stück 12):** nur als Hinweis; die Rundung ist eine Zuordnung.
- **Spektrale Ordnung (Fiedler):** nur als Satz (die Lösung ohne Anker unter einer Normierung).
- **Pads mit Größe, Lage am Rand des Bretts, Routing:** die Pads sind Punkte auf einem Ring.
- **Asymmetrische Flüsse und Abstände.**

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Streamlit Cloud: Python-Version in den App-Einstellungen prüfen (lokal Python 3.14, CI Python 3.12); der Code verwendet nur Merkmale, die in Python 3.12 laufen. <!-- lint-ok: dezimalpunkt -->

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy, pandas und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
