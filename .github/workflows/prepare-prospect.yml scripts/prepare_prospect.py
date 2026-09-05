name: ReviewSpot Interessent vorbereiten

on:
  workflow_dispatch:
    inputs:
      company_name:
        description: "Unternehmensname"
        required: true
        type: string
      place_id:
        description: "Google Place ID, z. B. ChIJ..."
        required: true
        type: string
      status:
        description: "Status"
        required: true
        default: "Vorbereitet"
        type: choice
        options:
          - Vorbereitet
          - Kontaktiert
          - Interessiert
          - Zahlung abgeschlossen
          - Kein Interesse

permissions:
  contents: write

concurrency:
  group: prospects-write
  cancel-in-progress: false

jobs:
  prepare-prospect:
    runs-on: ubuntu-latest

    steps:
      - name: Repository laden
        uses: actions/checkout@v4

      - name: Python einrichten
        uses: actions/setup-python@v5
        with:
          python-version: "3.x"

      - name: Interessent speichern
        env:
          COMPANY_NAME: ${{ inputs.company_name }}
          PLACE_ID: ${{ inputs.place_id }}
          STATUS: ${{ inputs.status }}
        run: python scripts/prepare_prospect.py

      - name: Änderungen speichern
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add data/prospects.csv

          if git diff --cached --quiet; then
            echo "Keine Änderungen vorhanden."
            exit 0
          fi

          git commit -m "Interessent vorbereiten: ${{ inputs.company_name }}"
          git push
