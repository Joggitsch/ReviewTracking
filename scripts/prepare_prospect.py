from __future__ import annotations

import csv
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote

DATA_DIR = Path("data")
PROSPECTS_FILE = DATA_DIR / "prospects.csv"

FIELDNAMES = [
    "Unternehmen",
    "Place ID",
    "Direkter Bewertungslink",
    "Google Maps Link",
    "Status",
]

ALLOWED_STATUSES = {
    "Vorbereitet",
    "Kontaktiert",
    "Interessiert",
    "Zahlung abgeschlossen",
    "Kein Interesse",
}


def load_prospects() -> list[dict[str, str]]:
    if not PROSPECTS_FILE.exists() or PROSPECTS_FILE.stat().st_size == 0:
        return []

    with PROSPECTS_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def save_prospects(rows: list[dict[str, str]]) -> None:
    DATA_DIR.mkdir(exist_ok=True)

    rows = sorted(rows, key=lambda row: row["Unternehmen"].casefold())

    with PROSPECTS_FILE.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


company_name = os.environ.get("COMPANY_NAME", "").strip()
place_id = os.environ.get("PLACE_ID", "").strip()
status = os.environ.get("STATUS", "Vorbereitet").strip()

if not company_name:
    sys.exit("Fehler: Unternehmensname fehlt.")

if not place_id:
    sys.exit("Fehler: Place ID fehlt.")

if not re.fullmatch(r"[A-Za-z0-9_-]{10,200}", place_id):
    sys.exit("Fehler: Place ID sieht ungültig aus.")

if status not in ALLOWED_STATUSES:
    sys.exit(f"Fehler: Unbekannter Status: {status}")

direct_review_url = (
    "https://search.google.com/local/writereview?placeid="
    + quote(place_id, safe="")
)

maps_url = (
    "https://www.google.com/maps/search/?api=1"
    "&query=" + quote(company_name)
    + "&query_place_id=" + quote(place_id, safe="")
)

new_row = {
    "Unternehmen": company_name,
    "Place ID": place_id,
    "Direkter Bewertungslink": direct_review_url,
    "Google Maps Link": maps_url,
    "Status": status,
}

rows = load_prospects()

# Gleiche Place ID = bestehenden Interessenten aktualisieren statt duplizieren.
updated = False
for index, row in enumerate(rows):
    if row.get("Place ID", "").strip() == place_id:
        rows[index] = new_row
        updated = True
        break

if not updated:
    rows.append(new_row)

save_prospects(rows)

summary = os.environ.get("GITHUB_STEP_SUMMARY")
if summary:
    action = "aktualisiert" if updated else "vorbereitet"
    Path(summary).write_text(
        f"## ReviewSpot Interessent {action}\n\n"
        f"**Unternehmen:** {company_name}\n\n"
        f"**Status:** {status}\n\n"
        f"**Place ID:** `{place_id}`\n\n"
        f"**Direkter Bewertungslink:** {direct_review_url}\n\n"
        f"**Google-Maps-Link:** {maps_url}\n\n"
        f"Die Übersicht liegt in `data/prospects.csv`.\n",
        encoding="utf-8",
    )
