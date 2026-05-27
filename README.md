# Text Anonymizer

Reversible text anonymization service as a Docker container. Detects personally identifiable information (PII) in text, replaces it with numbered placeholders, and returns a mapping table for later restoration — ideal for the workflow **Text > Anonymize > AI Processing > De-Anonymize**.

Based on [OpenAI Privacy Filter](https://github.com/openai/privacy-filter) (Apache 2.0).

## Workflow

```
┌───────────────┐     ┌──────────────────┐     ┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Original Text │────▶│  /anonymize      │────▶│ AI Service  │────▶│  /deanonymize    │────▶│ Final Text   │
│               │     │  + Exclusions    │     │ (ChatGPT,   │     │  + Mapping       │     │ (PII back)   │
│               │     │  → Mapping Table │     │  Claude etc.)│     │                  │     │              │
└───────────────┘     └──────────────────┘     └─────────────┘     └──────────────────┘     └──────────────┘
```

## Quick Start

```bash
docker compose up --build
```

The service is available at `http://localhost:8000`.

On the first request, the model is downloaded from HuggingFace (~600 MB). After that it is cached in the Docker volume `model-cache`.

## API Reference

### POST /anonymize

Anonymizes text and returns a mapping table for restoration.

**Request:**

```json
{
  "text": "Please contact John Smith at john.smith@example.com or +1 555-0123. He works at Levara, 42 Main Street, New York, NY 10001.",
  "exclusions": ["Levara"],
  "categories": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `string` | Yes | The text to anonymize |
| `exclusions` | `string[]` | No | Terms to **exclude** from anonymization (company names, technical terms, etc.) |
| `categories` | `string[]` | No | Only detect specific PII categories. `null` = all. Options: `person`, `email_address`, `phone_number`, `private_address`, `url`, `date`, `account_number`, `secret` |

**Response:**

```json
{
  "anonymized_text": "Please contact [PERSON_1] at [EMAIL_1] or [PHONE_1]. He works at Levara, [ADDRESS_1].",
  "mapping": {
    "[PERSON_1]": "John Smith",
    "[EMAIL_1]": "john.smith@example.com",
    "[PHONE_1]": "+1 555-0123",
    "[ADDRESS_1]": "42 Main Street, New York, NY 10001"
  },
  "entities": [
    {
      "placeholder": "[PERSON_1]",
      "original": "John Smith",
      "category": "person",
      "start": 15,
      "end": 25
    }
  ],
  "exclusions_applied": ["Levara"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `anonymized_text` | `string` | Text with numbered placeholders instead of PII |
| `mapping` | `object` | Placeholder-to-original-value mapping. **Keep this table!** |
| `entities` | `array` | Details for each detected entity (category, position, original) |
| `exclusions_applied` | `string[]` | Which exclusion terms were active |

### POST /deanonymize

Restores the original text by replacing placeholders with values from the mapping table.

**Request:**

```json
{
  "text": "The AI recommends contacting [PERSON_1] via [EMAIL_1].",
  "mapping": {
    "[PERSON_1]": "John Smith",
    "[EMAIL_1]": "john.smith@example.com"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `string` | Yes | The anonymized (and possibly AI-processed) text containing placeholders |
| `mapping` | `object` | Yes | The mapping table from the `/anonymize` response |

**Response:**

```json
{
  "restored_text": "The AI recommends contacting John Smith via john.smith@example.com.",
  "replacements_made": 2,
  "unresolved_placeholders": []
}
```

| Field | Type | Description |
|-------|------|-------------|
| `restored_text` | `string` | Text with original values restored |
| `replacements_made` | `int` | Number of placeholders that were replaced |
| `unresolved_placeholders` | `string[]` | Placeholders found in text that had no mapping entry (e.g. if AI invented new ones) |

### GET /health

```json
{"status": "ok"}
```

### POST /warmup

Pre-loads the model into memory (otherwise loaded on first `/anonymize` request).

## Placeholder Format

Placeholders follow the pattern `[CATEGORY_N]`:

| Placeholder | PII Category |
|-------------|-------------|
| `[PERSON_1]`, `[PERSON_2]`, ... | Person names |
| `[EMAIL_1]`, `[EMAIL_2]`, ... | Email addresses |
| `[PHONE_1]`, `[PHONE_2]`, ... | Phone numbers |
| `[ADDRESS_1]`, `[ADDRESS_2]`, ... | Addresses |
| `[URL_1]`, `[URL_2]`, ... | URLs |
| `[DATE_1]`, `[DATE_2]`, ... | Dates |
| `[ACCOUNT_1]`, `[ACCOUNT_2]`, ... | Account numbers |
| `[SECRET_1]`, `[SECRET_2]`, ... | Secrets (API keys, passwords) |

Numbering is sequential per category and stable within a single request.

## Exclusions

### Per Request

In the `exclusions` field of the request body:

```json
{
  "text": "...",
  "exclusions": ["Levara", "SAP", "Kubernetes"]
}
```

### Persistent (File-Based)

JSON files in the `exclusions/` directory are automatically loaded and merged with per-request exclusions. The directory is mounted as a read-only volume into the container.

**Format — Simple list:**

```json
["Levara", "SAP", "Deutsche Bank", "Kubernetes"]
```

**Format — Categorized:**

```json
{
  "companies": ["Levara", "SAP"],
  "customers": ["Deutsche Bank", "BMW"],
  "terms": ["Kubernetes", "OAuth2", "MCP", "BPMN"]
}
```

Both formats are supported. For categorized lists, all values from all categories are merged. Multiple files are supported (e.g. `companies.json`, `terms.json`).

### Matching Behavior

- **Case-insensitive**: "levara" matches "Levara"
- **Substring matching**: The exclusion term must appear as a contiguous string in the text
- **Overlap handling**: If a detected PII span overlaps with an exclusion term, the entire PII span is kept unchanged

## Example Workflow

### 1. Anonymize text

```bash
curl -X POST http://localhost:8000/anonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Dr. Smith from Levara Inc. signed a contract on 03/15/2025 with Jane Doe (jane.doe@company.com, phone 555-0199) for the Kubernetes migration project at 28 Leopold St, Munich 80802.",
    "exclusions": ["Levara", "Kubernetes"]
  }'
```

### 2. Send anonymized text to AI

```
Prompt to ChatGPT/Claude:
"Summarize the following contract matter:
[PERSON_1] from Levara Inc. signed a contract on [DATE_1] with
[PERSON_2] ([EMAIL_1], phone [PHONE_1]) for the Kubernetes migration project
at [ADDRESS_1]."
```

### 3. De-anonymize AI result

```bash
curl -X POST http://localhost:8000/deanonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "On [DATE_1], a contract was signed between [PERSON_1] (Levara Inc.) and [PERSON_2]. Contact: [EMAIL_1].",
    "mapping": {
      "[PERSON_1]": "Dr. Smith",
      "[PERSON_2]": "Jane Doe",
      "[EMAIL_1]": "jane.doe@company.com",
      "[PHONE_1]": "555-0199",
      "[DATE_1]": "03/15/2025",
      "[ADDRESS_1]": "28 Leopold St, Munich 80802"
    }
  }'
```

**Result:**
```
On 03/15/2025, a contract was signed between Dr. Smith (Levara Inc.) and Jane Doe. Contact: jane.doe@company.com.
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OPF_DEVICE` | `cpu` | `cpu` or `cuda` (GPU) |

## Development

```bash
# Local without Docker
pip install -r requirements.txt
uvicorn app.main:app --reload

# Tests
pip install pytest httpx
pytest
```

## Limitations

- The model is a **tool**, not a compliance guarantee (see [OpenAI notes](https://github.com/openai/privacy-filter#limitations))
- Uncommon names or regional formats may not be detected
- Very long texts (>128K tokens) are automatically split into windows

## License

Apache 2.0 (same as OpenAI Privacy Filter)
