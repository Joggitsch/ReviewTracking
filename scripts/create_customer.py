from __future__ import annotations

import csv
import html
import json
import os
import re
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import quote

BASE_URL = "https://reviewspot-de.github.io/ReviewTracking"
GOATCOUNTER_URL = "https://reviewspot.goatcounter.com/count"

DATA_DIR = Path("data")
CUSTOMERS_FILE = DATA_DIR / "customers.json"
HISTORY_FILE = DATA_DIR / "review_history.csv"
REVIEW_WORKFLOW = Path(".github/workflows/log-review.yml")


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def load_customers() -> list[dict]:
    if not CUSTOMERS_FILE.exists():
        return []
    return json.loads(CUSTOMERS_FILE.read_text(encoding="utf-8"))


def save_customers(customers: list[dict]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    customers = sorted(customers, key=lambda c: c["company_name"].casefold())
    CUSTOMERS_FILE.write_text(
        json.dumps(customers, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def rebuild_review_workflow(customers: list[dict]) -> None:
    slugs = [c["slug"] for c in sorted(customers, key=lambda c: c["company_name"].casefold())]
    options = "\n".join(f"          - {slug}" for slug in slugs)

    content = """name: Bewertungsstand eintragen

on:
  workflow_dispatch:
    inputs:
      company_slug:
        description: "Unternehmen"
        required: true
        type: choice
        options:
__OPTIONS__
      review_count:
        description: "Aktuelle Anzahl Google-Bewertungen"
        required: true
        type: string
      date:
        description: "Optional YYYY-MM-DD. Leer = heute."
        required: false
        type: string

permissions:
  contents: write

jobs:
  log-review:
    runs-on: ubuntu-latest

    steps:
      - name: Repository laden
        uses: actions/checkout@v4

      - name: Python einrichten
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Bewertungsstand speichern
        env:
          COMPANY_SLUG: ${{ inputs.company_slug }}
          REVIEW_COUNT: ${{ inputs.review_count }}
          SNAPSHOT_DATE: ${{ inputs.date }}
        run: python scripts/log_review.py

      - name: Änderungen speichern
        run: |
          git config user.name "ReviewSpot Automation"
          git config user.email "actions@users.noreply.github.com"
          git add data/ REVIEW_DASHBOARD.md .github/workflows/log-review.yml
          if git diff --cached --quiet; then
            echo "Keine Änderungen vorhanden."
          else
            git commit -m "Log review count for ${{ inputs.company_slug }}"
            git push
          fi
""".replace("__OPTIONS__", options)

    REVIEW_WORKFLOW.write_text(content, encoding="utf-8")


def append_initial_review(slug: str, review_text: str) -> None:
    review_text = review_text.strip()
    if not review_text:
        return

    if not review_text.isdigit():
        sys.exit("Fehler: initial_reviews muss eine ganze Zahl sein.")

    DATA_DIR.mkdir(exist_ok=True)
    new_file = not HISTORY_FILE.exists() or HISTORY_FILE.stat().st_size == 0

    with HISTORY_FILE.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["date", "company_slug", "review_count"])
        writer.writerow([date.today().isoformat(), slug, int(review_text)])


company_name = os.environ.get("COMPANY_NAME", "").strip()
place_id = os.environ.get("PLACE_ID", "").strip()
custom_slug = os.environ.get("SLUG", "").strip()
target_mode = os.environ.get("TARGET_MODE", "direct").strip().lower()
initial_reviews = os.environ.get("INITIAL_REVIEWS", "").strip()

if not company_name:
    sys.exit("Fehler: Unternehmensname fehlt.")

if not place_id:
    sys.exit("Fehler: Place ID fehlt.")

if target_mode not in {"direct", "maps"}:
    sys.exit("Fehler: TARGET_MODE muss direct oder maps sein.")

if not re.fullmatch(r"[A-Za-z0-9_-]{10,200}", place_id):
    sys.exit("Fehler: Place ID sieht ungültig aus.")

slug = slugify(custom_slug) if custom_slug else slugify(company_name)
if not slug:
    sys.exit("Fehler: Konnte keinen gültigen URL-Namen erzeugen.")

company_safe = html.escape(company_name)

direct_review_url = (
    "https://search.google.com/local/writereview?placeid="
    + quote(place_id, safe="")
)

maps_url = (
    "https://www.google.com/maps/search/?api=1"
    "&query=" + quote(company_name)
    + "&query_place_id=" + quote(place_id, safe="")
)

active_url = direct_review_url if target_mode == "direct" else maps_url
tracking_url = f"{BASE_URL}/{slug}/"

customer_dir = Path(slug)
customer_dir.mkdir(parents=True, exist_ok=True)
index_file = customer_dir / "index.html"

page = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <meta name="theme-color" content="#0b0b0c">
  <title>{company_safe} – Bewertung</title>

  <script
    data-goatcounter="{GOATCOUNTER_URL}"
    async
    src="https://gc.zgo.at/count.js"></script>

  <style>
    :root {{
      --bg:#0b0b0c;
      --text:#ffffff;
      --muted:#a9a9ad;
      --gold:#f4c542;
      --line:#2a2a2f;
    }}
    * {{ box-sizing:border-box; }}
    html, body {{
      margin:0;
      width:100%;
      min-height:100%;
      background:var(--bg);
      color:var(--text);
      font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
    }}
    body {{
      min-height:100vh;
      display:grid;
      place-items:center;
      padding:24px;
    }}
    .wrap {{ width:min(100%,430px); text-align:center; }}
    .eyebrow {{
      font-size:13px;
      letter-spacing:.16em;
      text-transform:uppercase;
      color:var(--muted);
      margin-bottom:14px;
    }}
    h1 {{
      margin:0;
      font-size:34px;
      line-height:1.1;
      font-weight:800;
      letter-spacing:-.03em;
    }}
    .stars {{
      margin:18px 0 12px;
      font-size:25px;
      letter-spacing:5px;
      color:var(--gold);
      white-space:nowrap;
    }}
    .message {{
      margin:0 auto;
      max-width:320px;
      color:var(--muted);
      font-size:16px;
      line-height:1.5;
    }}
    .loader {{
      width:180px;
      height:4px;
      background:var(--line);
      border-radius:999px;
      overflow:hidden;
      margin:24px auto 0;
    }}
    .loader span {{
      display:block;
      width:40%;
      height:100%;
      border-radius:999px;
      background:var(--text);
      animation:load .65s ease-out forwards;
      transform-origin:left;
    }}
    .fallback {{
      margin-top:22px;
      font-size:13px;
      color:#77777c;
    }}
    .fallback a {{
      color:#b8b8bc;
      text-decoration:none;
      border-bottom:1px solid #44444a;
    }}
    @keyframes load {{
      from {{ transform:scaleX(.05); opacity:.5; }}
      to {{ transform:scaleX(2.5); opacity:1; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .loader span {{ animation:none; width:100%; }}
    }}
  </style>

  <script>
    const targetMode = {target_mode!r};
    const directReviewUrl = {direct_review_url!r};
    const mapsUrl = {maps_url!r};
    const targetUrl = targetMode === "maps" ? mapsUrl : directReviewUrl;

    window.addEventListener("load", function () {{
      setTimeout(function () {{
        window.location.replace(targetUrl);
      }}, 450);
    }});

    setTimeout(function () {{
      window.location.replace(targetUrl);
    }}, 1800);
  </script>
</head>

<body>
  <main class="wrap" aria-live="polite">
    <div class="eyebrow">Google Bewertung</div>
    <h1>{company_safe}</h1>
    <div class="stars" aria-label="5 Sterne">★★★★★</div>
    <p class="message">Bewertungsfenster wird geöffnet …</p>
    <div class="loader" aria-hidden="true"><span></span></div>
    <p class="fallback">
      Falls nichts passiert,
      <a href="{active_url}">hier öffnen</a>.
    </p>
  </main>
</body>
</html>
"""

index_file.write_text(page, encoding="utf-8")

(customer_dir / "customer.txt").write_text(
    f"Unternehmen: {company_name}\n"
    f"Place ID: {place_id}\n"
    f"Slug: {slug}\n"
    f"Modus: {target_mode}\n"
    f"Tracking-Link: {tracking_url}\n"
    f"Direkter Review-Link: {direct_review_url}\n"
    f"Google-Maps-Link: {maps_url}\n",
    encoding="utf-8",
)

customers = [c for c in load_customers() if c.get("slug") != slug]
customers.append({
    "company_name": company_name,
    "slug": slug,
    "place_id": place_id,
    "target_mode": target_mode,
    "tracking_url": tracking_url,
    "direct_review_url": direct_review_url,
    "maps_url": maps_url,
})
save_customers(customers)
rebuild_review_workflow(customers)
append_initial_review(slug, initial_reviews)

subprocess.check_call(["python", "scripts/build_review_dashboard.py"])

summary = os.environ.get("GITHUB_STEP_SUMMARY")
if summary:
    Path(summary).write_text(
        f"## ReviewSpot Kunde erstellt/aktualisiert\n\n"
        f"**Unternehmen:** {company_name}\n\n"
        f"**Modus:** {target_mode}\n\n"
        f"**Tracking-Link:** {tracking_url}\n\n"
        f"**Direkter Review-Link:** {direct_review_url}\n\n"
        f"**Google-Maps-Link:** {maps_url}\n",
        encoding="utf-8",
    )

