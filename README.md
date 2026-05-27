# Text Anonymizer

Reversibler Text-Anonymisierungsdienst als Docker-Container. Erkennt personenbezogene Daten (PII) in Texten, ersetzt sie durch nummerierte Platzhalter und liefert eine Mapping-Tabelle zur späteren Wiederherstellung — ideal für den Workflow **Text → Anonymisierung → KI-Verarbeitung → De-Anonymisierung**.

Basiert auf [OpenAI Privacy Filter](https://github.com/openai/privacy-filter) (Apache 2.0).

## Workflow

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Originaltext │────▶│  /anonymize      │────▶│ KI-Dienst   │────▶│  /deanonymize    │────▶│ Finaler Text │
│              │     │  + Exclusions    │     │ (ChatGPT,   │     │  + Mapping       │     │ (PII zurück) │
│              │     │  → Mapping-Table │     │  Claude etc.)│     │                  │     │              │
└─────────────┘     └──────────────────┘     └─────────────┘     └──────────────────┘     └──────────────┘
```

## Schnellstart

```bash
docker compose up --build
```

Der Service ist erreichbar unter `http://localhost:8000`.

Beim ersten Request wird das Modell von HuggingFace heruntergeladen (~600 MB). Danach ist es im Docker-Volume `model-cache` gecacht.

## API-Referenz

### POST /anonymize

Anonymisiert Text und liefert eine Mapping-Tabelle zur Wiederherstellung.

**Request:**

```json
{
  "text": "Bitte kontaktieren Sie Max Mustermann unter max.mustermann@example.com oder +49 171 1234567. Er arbeitet bei Levara in der Hauptstraße 42, 10115 Berlin.",
  "exclusions": ["Levara"],
  "categories": null
}
```

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| `text` | `string` | Ja | Der zu anonymisierende Text |
| `exclusions` | `string[]` | Nein | Begriffe, die **nicht** anonymisiert werden (Firmennamen, Fachbegriffe etc.) |
| `categories` | `string[]` | Nein | Nur bestimmte PII-Kategorien erkennen. `null` = alle. Optionen: `person`, `email_address`, `phone_number`, `private_address`, `url`, `date`, `account_number`, `secret` |

**Response:**

```json
{
  "anonymized_text": "Bitte kontaktieren Sie [PERSON_1] unter [EMAIL_1] oder [PHONE_1]. Er arbeitet bei Levara in der [ADDRESS_1].",
  "mapping": {
    "[PERSON_1]": "Max Mustermann",
    "[EMAIL_1]": "max.mustermann@example.com",
    "[PHONE_1]": "+49 171 1234567",
    "[ADDRESS_1]": "Hauptstraße 42, 10115 Berlin"
  },
  "entities": [
    {
      "placeholder": "[PERSON_1]",
      "original": "Max Mustermann",
      "category": "person",
      "start": 22,
      "end": 36
    }
  ],
  "exclusions_applied": ["Levara"]
}
```

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `anonymized_text` | `string` | Text mit nummerierten Platzhaltern anstelle der PII |
| `mapping` | `object` | Zuordnung Platzhalter → Originalwert. **Diese Tabelle aufbewahren!** |
| `entities` | `array` | Details zu jedem erkannten Element (Kategorie, Position, Original) |
| `exclusions_applied` | `string[]` | Welche Ausschluss-Begriffe aktiv waren |

### POST /deanonymize

Stellt den Originaltext wieder her, indem Platzhalter durch die Werte aus der Mapping-Tabelle ersetzt werden.

**Request:**

```json
{
  "text": "Die KI empfiehlt, dass [PERSON_1] per [EMAIL_1] kontaktiert wird.",
  "mapping": {
    "[PERSON_1]": "Max Mustermann",
    "[EMAIL_1]": "max.mustermann@example.com"
  }
}
```

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| `text` | `string` | Ja | Der anonymisierte (und ggf. KI-verarbeitete) Text mit Platzhaltern |
| `mapping` | `object` | Ja | Die Mapping-Tabelle aus der `/anonymize`-Response |

**Response:**

```json
{
  "restored_text": "Die KI empfiehlt, dass Max Mustermann per max.mustermann@example.com kontaktiert wird.",
  "replacements_made": 2,
  "unresolved_placeholders": []
}
```

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `restored_text` | `string` | Text mit wiederhergestellten Originalwerten |
| `replacements_made` | `int` | Anzahl der ersetzten Platzhalter |
| `unresolved_placeholders` | `string[]` | Platzhalter im Text, für die kein Mapping existiert (z.B. wenn KI neue erfunden hat) |

### GET /health

```json
{"status": "ok"}
```

### POST /warmup

Lädt das Modell vorab in den Speicher (sonst beim ersten `/anonymize`-Request).

## Platzhalter-Format

Platzhalter folgen dem Schema `[KATEGORIE_N]`:

| Platzhalter | PII-Kategorie |
|-------------|---------------|
| `[PERSON_1]`, `[PERSON_2]`, ... | Personennamen |
| `[EMAIL_1]`, `[EMAIL_2]`, ... | E-Mail-Adressen |
| `[PHONE_1]`, `[PHONE_2]`, ... | Telefonnummern |
| `[ADDRESS_1]`, `[ADDRESS_2]`, ... | Adressen |
| `[URL_1]`, `[URL_2]`, ... | URLs |
| `[DATE_1]`, `[DATE_2]`, ... | Datumsangaben |
| `[ACCOUNT_1]`, `[ACCOUNT_2]`, ... | Kontonummern |
| `[SECRET_1]`, `[SECRET_2]`, ... | Geheimnisse (API-Keys, Passwörter) |

Die Nummerierung ist pro Kategorie fortlaufend und stabil innerhalb eines Requests.

## Exclusions (Ausschluss-Liste)

### Per Request

Im `exclusions`-Feld des Request-Body:

```json
{
  "text": "...",
  "exclusions": ["Levara", "SAP", "Kubernetes"]
}
```

### Persistent (Datei)

JSON-Dateien im Verzeichnis `exclusions/` werden automatisch geladen und mit Request-Exclusions zusammengeführt. Das Verzeichnis wird als Read-Only-Volume in den Container gemounted.

**Format — Einfache Liste:**

```json
["Levara", "SAP", "Deutsche Bank", "Kubernetes"]
```

**Format — Kategorisiert:**

```json
{
  "companies": ["Levara", "SAP"],
  "customers": ["Deutsche Bank", "BMW"],
  "terms": ["Kubernetes", "OAuth2", "MCP", "BPMN"]
}
```

Beide Formate werden unterstützt. Bei kategorisierten Listen werden alle Werte aus allen Kategorien zusammengeführt. Mehrere Dateien möglich (z.B. `companies.json`, `terms.json`).

### Matching-Verhalten

- **Case-insensitive**: "levara" matcht "Levara"
- **Substring-Matching**: Der Ausschluss-Begriff muss als zusammenhängendes Wort im Text vorkommen
- **Überlappung**: Wenn ein erkanntes PII-Element mit einem Ausschluss-Begriff überlappt, wird das gesamte PII-Element beibehalten

## Beispiel-Workflow

### 1. Text anonymisieren

```bash
curl -X POST http://localhost:8000/anonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Herr Dr. Schmidt von der Levara GmbH hat am 15.03.2025 einen Vertrag mit Frau Müller (anna.mueller@firma.de, Tel. 089-12345) über das Kubernetes-Migrationsprojekt in der Leopoldstraße 28, 80802 München unterzeichnet.",
    "exclusions": ["Levara", "Kubernetes"]
  }'
```

### 2. Anonymisierten Text an KI senden

```
Prompt an ChatGPT/Claude:
"Fasse folgenden Vertragssachverhalt zusammen:
Herr [PERSON_1] von der Levara GmbH hat am [DATE_1] einen Vertrag mit
[PERSON_2] ([EMAIL_1], Tel. [PHONE_1]) über das Kubernetes-Migrationsprojekt
in der [ADDRESS_1] unterzeichnet."
```

### 3. KI-Ergebnis de-anonymisieren

```bash
curl -X POST http://localhost:8000/deanonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Am [DATE_1] wurde ein Vertrag zwischen [PERSON_1] (Levara GmbH) und [PERSON_2] geschlossen. Kontakt: [EMAIL_1].",
    "mapping": {
      "[PERSON_1]": "Dr. Schmidt",
      "[PERSON_2]": "Frau Müller",
      "[EMAIL_1]": "anna.mueller@firma.de",
      "[PHONE_1]": "089-12345",
      "[DATE_1]": "15.03.2025",
      "[ADDRESS_1]": "Leopoldstraße 28, 80802 München"
    }
  }'
```

**Ergebnis:**
```
Am 15.03.2025 wurde ein Vertrag zwischen Dr. Schmidt (Levara GmbH) und Frau Müller geschlossen. Kontakt: anna.mueller@firma.de.
```

## Konfiguration

| Umgebungsvariable | Standard | Beschreibung |
|-------------------|----------|--------------|
| `OPF_DEVICE` | `cpu` | `cpu` oder `cuda` (GPU) |

## Entwicklung

```bash
# Lokal ohne Docker
pip install -r requirements.txt
uvicorn app.main:app --reload

# Tests
pip install pytest httpx
pytest
```

## Einschränkungen

- Das Modell ist ein **Hilfsmittel**, keine Compliance-Garantie (siehe [OpenAI-Hinweise](https://github.com/openai/privacy-filter#limitations))
- Ungewöhnliche Namen oder regionale Formate werden möglicherweise nicht erkannt
- Bei sehr langen Texten (>128K Tokens) wird automatisch in Fenster aufgeteilt

## Lizenz

Apache 2.0 (wie OpenAI Privacy Filter)
