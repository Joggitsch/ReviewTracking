import csv
import json
import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

DATA = Path("data")
CUSTOMERS_FILE = DATA / "customers.json"
HISTORY_FILE = DATA / "review_history.csv"

slug = os.environ.get("COMPANY_SLUG", "").strip()
review_text = os.environ.get("REVIEW_COUNT", "").strip()
snapshot_date = os.environ.get("SNAPSHOT_DATE", "").strip() or date.today().isoformat()

if not review_text.isdigit():
    sys.exit("Fehler: Bewertungszahl muss eine ganze Zahl sein.")

try:
    datetime.strptime(snapshot_date, "%Y-%m-%d")
except ValueError:
    sys.exit("Fehler: Datum muss YYYY-MM-DD sein.")

customers = json.loads(CUSTOMERS_FILE.read_text(encoding="utf-8"))
customer = next((c for c in customers if c.get("slug") == slug), None)

if not customer:
    sys.exit(f"Fehler: Unternehmen '{slug}' nicht gefunden.")

previous = None

if HISTORY_FILE.exists() and HISTORY_FILE.stat().st_size > 0:
    with HISTORY_FILE.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    matches = [r for r in rows if r.get("company_slug") == slug]
    if matches:
        previous = int(matches[-1]["review_count"])

new_file = not HISTORY_FILE.exists() or HISTORY_FILE.stat().st_size == 0

with HISTORY_FILE.open("a", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    if new_file:
        writer.writerow(["date", "company_slug", "review_count"])
    writer.writerow([snapshot_date, slug, int(review_text)])

subprocess.check_call(["python", "scripts/build_review_dashboard.py"])

delta = None if previous is None else int(review_text) - previous
delta_text = "erster Messpunkt" if delta is None else f"{delta:+d}"

summary = os.environ.get("GITHUB_STEP_SUMMARY")
if summary:
    Path(summary).write_text(
        f"## Bewertungsstand gespeichert\n\n"
        f"**Unternehmen:** {customer['company_name']}\n\n"
        f"**Datum:** {snapshot_date}\n\n"
        f"**Google-Bewertungen:** {review_text}\n\n"
        f"**Veränderung zum letzten Messpunkt:** {delta_text}\n\n"
        f"**Google Maps:** {customer['maps_url']}\n\n"
        f"**Tracking-Link:** {customer['tracking_url']}\n",
        encoding="utf-8",
    )
