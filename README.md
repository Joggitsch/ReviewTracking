# ReviewTracking

Öffentliches ReviewSpot-Repository für Tracking-Links und die manuelle Historie von Google-Bewertungsständen.

## Was das Repository macht

Für jedes Unternehmen existiert ein stabiler ReviewSpot-Link, z. B.:

`https://reviewspot-de.github.io/ReviewTracking/eiscafe-fantasia/`

Dieser Link wird auf NFC-Chips bzw. QR-Ziele geschrieben. Die physische URL bleibt gleich.

Danach leitet die Seite – je nach hinterlegtem Modus – weiter zu:

- `direct` → direktes Google-Bewertungsfenster
- `maps` → Google-Maps-Unternehmensseite

Das Ziel kann später remote geändert werden, ohne den NFC-Chip erneut zu beschreiben.

Die Zwischen-Seite enthält GoatCounter und kann dadurch Aufrufe des Tracking-Links zählen.

## Aktuelle Unternehmen

Die technische Kundenliste liegt in:

`data/customers.json`

Sie enthält ausschließlich öffentliche/technische Betriebsinformationen:

- Unternehmensname
- Slug
- Google Place ID
- Zielmodus
- Tracking-Link
- direkter Bewertungslink
- Google-Maps-Link

## GitHub Actions

### ReviewSpot Kunde anlegen oder aktualisieren

Workflow:

`.github/workflows/new-customer.yml`

Eingaben:

- Unternehmensname
- Place ID
- optionaler Slug
- `direct` oder `maps`
- optionaler initialer Bewertungsstand

Der Slug kann im Normalfall leer bleiben und wird aus dem Unternehmensnamen erzeugt.

Beim Anlegen/Aktualisieren werden automatisch:

- Tracking-Seite erzeugt
- `customer.txt` erzeugt
- `data/customers.json` aktualisiert
- Dropdown im Review-Workflow aktualisiert
- Review-Dashboard aktualisiert

### Bewertungsstand eintragen

Workflow:

`.github/workflows/log-review.yml`

Unternehmen auswählen, aktuelle Anzahl der Google-Bewertungen eingeben und das Datum optional leer lassen.

Leer = heutiges Datum.

Gespeichert wird in:

`data/review_history.csv`

Danach wird automatisch `REVIEW_DASHBOARD.md` aktualisiert.

## Review-Dashboard

Dashboard:

`REVIEW_DASHBOARD.md`

Enthält:

- Anzahl angelegter Unternehmen
- Anzahl der Unternehmen mit Messwerten
- Anzahl der Messpunkte
- Start- und aktuellen Bewertungsstand
- Veränderung seit dem ersten Messpunkt
- letzte Messung
- Google-Maps-Link
- Tracking-Link
- komplette Historie je Unternehmen

## Dateien

### `data/customers.json`

Registry aller angelegten Unternehmen.

### `data/review_history.csv`

Historische manuelle Bewertungsstände:

```text
date,company_slug,review_count
```

### `scripts/create_customer.py`

Erzeugt/aktualisiert Tracking-Seiten und Kunden-Registry.

### `scripts/log_review.py`

Speichert einen neuen Bewertungsmesspunkt.

### `scripts/build_review_dashboard.py`

Baut das Review-Dashboard aus Registry und Historie neu auf.

## Messlogik

GoatCounter-Aufrufe und Veränderungen der Google-Bewertungszahl können gemeinsam betrachtet werden.

Wichtig: Daraus entsteht keine exakte Conversion Rate. Neue Google-Bewertungen können auch organisch oder über andere Kanäle entstanden sein.

Das System ist bewusst als einfache interne Verlaufs- und Plausibilitätsmessung gebaut.

## GitHub-Einstellung

Unter:

**Settings → Actions → General → Workflow permissions**

muss aktiviert sein:

**Read and write permissions**

damit die Workflows Änderungen zurück ins Repository schreiben können.
