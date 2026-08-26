import csv
import json
from collections import defaultdict
from pathlib import Path

DATA = Path("data")
CUSTOMERS_FILE = DATA / "customers.json"
HISTORY_FILE = DATA / "review_history.csv"

customers = json.loads(CUSTOMERS_FILE.read_text(encoding="utf-8"))

history = []
if HISTORY_FILE.exists() and HISTORY_FILE.stat().st_size > 0:
    with HISTORY_FILE.open("r", encoding="utf-8", newline="") as f:
        history = list(csv.DictReader(f))

by_company = defaultdict(list)
for row in history:
    by_company[row["company_slug"]].append(row)

for slug in by_company:
    by_company[slug].sort(key=lambda r: r["date"])

rows = []
measured = 0
total_growth = 0

for customer in sorted(customers, key=lambda c: c["company_name"].casefold()):
    measurements = by_company.get(customer["slug"], [])

    if measurements:
        measured += 1
        first = int(measurements[0]["review_count"])
        latest = int(measurements[-1]["review_count"])
        delta = latest - first
        total_growth += delta
        first_text = str(first)
        latest_text = str(latest)
        delta_text = f"{delta:+d}"
        last_date = measurements[-1]["date"]
        points = str(len(measurements))
    else:
        first_text = "–"
        latest_text = "–"
        delta_text = "–"
        last_date = "–"
        points = "0"

    rows.append(
        f"| {customer['company_name']} | {first_text} | {latest_text} | "
        f"{delta_text} | {points} | {last_date} | "
        f"[Maps]({customer['maps_url']}) | [Tracking]({customer['tracking_url']}) |"
    )

history_sections = []
for customer in sorted(customers, key=lambda c: c["company_name"].casefold()):
    measurements = by_company.get(customer["slug"], [])
    history_sections.append(f"### {customer['company_name']}")
    if not measurements:
        history_sections.append("\nNoch kein Bewertungsstand erfasst.\n")
        continue

    history_sections.append("\n| Datum | Bewertungen | Veränderung |\n|---|---:|---:|")
    previous = None
    for r in measurements:
        count = int(r["review_count"])
        delta = "–" if previous is None else f"{count - previous:+d}"
        history_sections.append(f"| {r['date']} | {count} | {delta} |")
        previous = count
    history_sections.append("")

dashboard = f"""# ReviewSpot Review Dashboard

## Überblick

| Kennzahl | Wert |
|---|---:|
| Angelegte Unternehmen | **{len(customers)}** |
| Unternehmen mit Messwerten | **{measured}** |
| Erfasste Messpunkte | **{len(history)}** |
| Summierte Veränderung seit erstem Messpunkt* | **{total_growth:+d} Reviews** |

\\* Nur über Unternehmen mit mindestens einem Messpunkt. Die Zahl zeigt eine Entwicklung,
keine sichere Attribution an ReviewSpot.

## Unternehmen

| Unternehmen | Start | Aktuell | Veränderung | Messpunkte | Letzte Messung | Google Maps | Tracking |
|---|---:|---:|---:|---:|---|---|---|
{chr(10).join(rows)}

## Review-Historie

{chr(10).join(history_sections)}

## Nutzung

Unter **Actions → Bewertungsstand eintragen**:

1. Unternehmen auswählen.
2. aktuelle Google-Bewertungszahl eintragen.
3. Datum leer lassen = heute.
4. Workflow starten.

Der neue Messpunkt wird in `data/review_history.csv` gespeichert und dieses Dashboard automatisch aktualisiert.

## Wichtiger Hinweis

Die Veränderung der öffentlich sichtbaren Google-Bewertungen darf nicht als exakte
Conversion Rate interpretiert werden. Bewertungen können auch organisch oder über
andere Wege entstanden sein. Das Dashboard dient als interne Verlaufs- und
Plausibilitätsmessung.
"""

Path("REVIEW_DASHBOARD.md").write_text(dashboard, encoding="utf-8")
