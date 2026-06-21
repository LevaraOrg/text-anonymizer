# Text Anonymizer

Reversible text anonymization service as a Docker container. Combines **AI-based PII detection** with **user-defined protected terms** to ensure both personal data and business secrets are masked before sending text to AI services. Returns a mapping table so the original values can be restored after AI processing.

Based on [OpenAI Privacy Filter](https://github.com/openai/privacy-filter) (Apache 2.0).

## Two Anonymization Modes

| Mode | What it does | Example |
|------|-------------|---------|
| **PII model** (automatic) | Detects standard personal data: names, emails, phones, addresses, dates | "Sarah Miller" → `[PERSON_1]` |
| **Protected terms** (user-defined) | Force-anonymizes business secrets, company names, project codes, domain jargon | "Levara" → `[COMPANY_1]` |

Both modes work together. The PII model catches what it knows; protected terms catch everything else you want hidden.

## Workflow

```
┌───────────────┐     ┌──────────────────────────────┐     ┌────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Original Text │────▶│  POST /anonymize              │────▶│ AI Service │────▶│  POST /deanonymize│────▶│ Final Text   │
│               │     │  + protected_terms (secrets)  │     │ (ChatGPT,  │     │  + mapping table │     │ (all values  │
│               │     │  + exclusions (keep visible)  │     │  Claude)   │     │                  │     │  restored)   │
│               │     │  → mapping table              │     │            │     │                  │     │              │
└───────────────┘     └──────────────────────────────┘     └────────────┘     └──────────────────┘     └──────────────┘
```

## Quick Start

### Option 1: Pull from GitHub Container Registry (recommended)

```bash
docker run -p 8000:8000 ghcr.io/levaraorg/text-anonymizer:latest
```

> **`unauthorized` error?** The published image must be public for an anonymous
> pull to work. If you get `Error response from daemon: ... unauthorized`, either:
>
> 1. **Make the package public** (one-time, recommended): open
>    <https://github.com/orgs/LevaraOrg/packages/container/text-anonymizer/settings>
>    → *Danger Zone* → *Change visibility* → **Public**. After that the command
>    above works for everyone with no login.
> 2. **Or authenticate** before pulling (keeps the image private):
>    ```bash
>    echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
>    docker run -p 8000:8000 ghcr.io/levaraorg/text-anonymizer:latest
>    ```
>    where `$GITHUB_TOKEN` is a personal access token with the `read:packages` scope.

With persistent model cache and custom protected terms:

```bash
docker run -p 8000:8000 \
  -v text-anonymizer-models:/root/.cache/huggingface \
  -v ./protected_terms:/app/protected_terms:ro \
  -v ./exclusions:/app/exclusions:ro \
  ghcr.io/levaraorg/text-anonymizer:latest
```

### Option 2: Build from source

```bash
git clone https://github.com/LevaraOrg/text-anonymizer.git
cd text-anonymizer
docker compose up --build
```

The service is available at `http://localhost:8000`. Interactive API docs at `http://localhost:8000/docs`.

On the first request, the model is downloaded from HuggingFace (~600 MB). After that it is cached in a Docker volume.

## API Reference

### POST /anonymize

Anonymizes text using both the PII model and user-defined protected terms. Returns anonymized text plus a mapping table for later restoration.

**Request:**

```json
{
  "text": "Sarah Miller from Levara signed the OrcaEngine contract with Acme Corp. Contact: sarah.miller@levara.cloud, +1 555-0198.",
  "protected_terms": {
    "COMPANY": ["Levara"],
    "CUSTOMER": ["Acme Corp"],
    "PROJECT": ["OrcaEngine"]
  },
  "exclusions": [],
  "categories": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `string` | Yes | The text to anonymize |
| `protected_terms` | `object` | No | Terms to **always anonymize**, grouped by custom category. Keys become placeholder prefixes. |
| `exclusions` | `string[]` | No | Terms to **never anonymize** — they stay visible even if the model detects them |
| `categories` | `string[]` | No | Filter PII model to specific categories. `null` = all. Options: `person`, `email_address`, `phone_number`, `private_address`, `url`, `date`, `account_number`, `secret` |

**Response:**

```json
{
  "anonymized_text": "[PERSON_1] from [COMPANY_1] signed the [PROJECT_1] contract with [CUSTOMER_1]. Contact: [EMAIL_1], [PHONE_1].",
  "mapping": {
    "[PERSON_1]": "Sarah Miller",
    "[COMPANY_1]": "Levara",
    "[PROJECT_1]": "OrcaEngine",
    "[CUSTOMER_1]": "Acme Corp",
    "[EMAIL_1]": "sarah.miller@levara.cloud",
    "[PHONE_1]": "+1 555-0198"
  },
  "entities": [
    {
      "placeholder": "[PERSON_1]",
      "original": "Sarah Miller",
      "category": "person",
      "start": 0,
      "end": 12
    },
    {
      "placeholder": "[COMPANY_1]",
      "original": "Levara",
      "category": "company",
      "start": 18,
      "end": 24
    }
  ],
  "exclusions_applied": [],
  "protected_terms_applied": {
    "COMPANY": ["Levara"],
    "CUSTOMER": ["Acme Corp"],
    "PROJECT": ["OrcaEngine"]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `anonymized_text` | `string` | Text with all sensitive content replaced by numbered placeholders |
| `mapping` | `object` | Placeholder-to-original-value mapping. **Keep this table!** |
| `entities` | `array` | Details for each replacement (category, position, original) |
| `exclusions_applied` | `string[]` | Which exclusion terms were active |
| `protected_terms_applied` | `object` | Which custom terms were force-anonymized |

### POST /deanonymize

Restores the original text by replacing placeholders with values from the mapping table. Works on AI-modified text — the AI can rearrange, summarize, or restructure the text as long as placeholders stay intact.

**Request:**

```json
{
  "text": "Summary: [PERSON_1] from [COMPANY_1] confirmed the [PROJECT_1] contract with [CUSTOMER_1]. Contact via [EMAIL_1].",
  "mapping": {
    "[PERSON_1]": "Sarah Miller",
    "[COMPANY_1]": "Levara",
    "[PROJECT_1]": "OrcaEngine",
    "[CUSTOMER_1]": "Acme Corp",
    "[EMAIL_1]": "sarah.miller@levara.cloud",
    "[PHONE_1]": "+1 555-0198"
  }
}
```

**Response:**

```json
{
  "restored_text": "Summary: Sarah Miller from Levara confirmed the OrcaEngine contract with Acme Corp. Contact via sarah.miller@levara.cloud.",
  "replacements_made": 5,
  "unresolved_placeholders": []
}
```

### GET /health

```json
{"status": "ok"}
```

### POST /warmup

Pre-loads the model into memory (otherwise loaded on first `/anonymize` request).

## MCP Server (Claude Desktop & other AI clients)

The same container also exposes an **MCP server** over Streamable HTTP at `/mcp`, so AI
clients like Claude Desktop can anonymize and restore text through tool calls. The MCP
tools run in-process — they share the loaded model with the REST API, no extra service.

| MCP tool | Maps to | Purpose |
|----------|---------|---------|
| `anonymize` | `POST /anonymize` | Replace PII + protected terms with reversible placeholders, returns the mapping table |
| `deanonymize` | `POST /deanonymize` | Restore original values from the mapping table |

**Endpoint:** `http://localhost:8000/mcp`

### Connect from Claude Desktop

1. Start the container so the endpoint is live:

   ```bash
   docker compose up -d
   ```

2. Add the server to your Claude Desktop config (`claude_desktop_config.json` —
   *Settings → Developer → Edit Config*). Claude Desktop launches stdio servers, so the
   [`mcp-remote`](https://www.npmjs.com/package/mcp-remote) bridge connects it to the
   HTTP endpoint (requires Node.js):

   ```json
   {
     "mcpServers": {
       "text-anonymizer": {
         "command": "npx",
         "args": ["-y", "mcp-remote", "http://localhost:8000/mcp"]
       }
     }
   }
   ```

3. Restart Claude Desktop. The `anonymize` and `deanonymize` tools appear under the
   text-anonymizer connector.

> **Typical use:** ask Claude to *"anonymize this before we work on it"* — it calls
> `anonymize`, processes the placeholdered text, then `deanonymize` restores the
> originals using the mapping it kept. Business secrets stay local; only placeholders
> ever reach the cloud model.

Any MCP client that speaks Streamable HTTP (e.g. the MCP Inspector) can connect directly
to `http://localhost:8000/mcp` without the bridge.

## Placeholder Format

Placeholders follow the pattern `[CATEGORY_N]`:

**PII model categories (auto-detected):**

| Placeholder | Detects |
|-------------|---------|
| `[PERSON_1]` | Person names |
| `[EMAIL_1]` | Email addresses |
| `[PHONE_1]` | Phone numbers |
| `[ADDRESS_1]` | Physical addresses |
| `[URL_1]` | URLs |
| `[DATE_1]` | Dates |
| `[ACCOUNT_1]` | Account numbers |
| `[SECRET_1]` | Secrets (API keys, passwords) |

**Custom categories (user-defined via `protected_terms`):**

You choose the category names. Common examples:

| Placeholder | Use for |
|-------------|---------|
| `[COMPANY_1]` | Your company name, subsidiaries |
| `[CUSTOMER_1]` | Client/customer names |
| `[PROJECT_1]` | Internal project names, codenames |
| `[PRODUCT_1]` | Product names not yet public |
| `[TERM_1]` | Domain jargon, proprietary methods |

## Protected Terms

### Per Request

In the `protected_terms` field — a dict where keys are category names and values are term lists:

```json
{
  "text": "...",
  "protected_terms": {
    "COMPANY": ["Levara", "LevaraOrg"],
    "CUSTOMER": ["Acme Corp", "BMW"],
    "PROJECT": ["OrcaEngine", "Project Phoenix"],
    "TERM": ["Kubernetes", "BPMN"]
  }
}
```

### Persistent (File-Based)

JSON files in the `protected_terms/` directory are automatically loaded and merged with per-request terms. The directory is mounted as a read-only volume into the container.

```json
{
  "COMPANY": ["Levara", "LevaraOrg"],
  "CUSTOMER": [],
  "PROJECT": ["OrcaEngine"],
  "TERM": ["Kubernetes", "OAuth2", "MCP"]
}
```

Multiple files are supported (e.g. `companies.json`, `projects.json`).

### Matching Behavior

- **Case-insensitive**: "levara" matches "Levara"
- **All occurrences**: Every instance in the text is replaced
- **Longer matches win**: "Acme Corp International" takes priority over "Acme Corp" when both overlap

## Exclusions

Terms to **keep visible** even if the PII model would anonymize them.

### Per Request

```json
{
  "text": "...",
  "exclusions": ["Springfield", "Illinois"]
}
```

### Persistent (File-Based)

JSON files in the `exclusions/` directory — either a flat list or a categorized dict:

```json
["Springfield", "New York"]
```

## Example Workflow

### 1. Anonymize text with business secrets

```bash
curl -X POST http://localhost:8000/anonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Dr. Smith from Levara signed a contract on 03/15/2025 with Jane Doe (jane.doe@company.com, phone 555-0199) for the OrcaEngine migration at Acme Corp, 28 Leopold St, Munich 80802.",
    "protected_terms": {
      "COMPANY": ["Levara"],
      "CUSTOMER": ["Acme Corp"],
      "PROJECT": ["OrcaEngine"]
    }
  }'
```

**Result — everything sensitive is masked:**
```
[PERSON_1] from [COMPANY_1] signed a contract on [DATE_1] with [PERSON_2]
([EMAIL_1], phone [PHONE_1]) for the [PROJECT_1] migration at [CUSTOMER_1],
[ADDRESS_1].
```

### 2. Send anonymized text to AI

```
Prompt to ChatGPT/Claude:
"Summarize this contract:
[PERSON_1] from [COMPANY_1] signed a contract on [DATE_1] with [PERSON_2]
([EMAIL_1], phone [PHONE_1]) for the [PROJECT_1] migration at [CUSTOMER_1],
[ADDRESS_1]."
```

The AI sees **no real names, no company names, no project names**. It works entirely with placeholders.

### 3. De-anonymize AI result

```bash
curl -X POST http://localhost:8000/deanonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "On [DATE_1], [PERSON_1] ([COMPANY_1]) and [PERSON_2] ([CUSTOMER_1]) signed a [PROJECT_1] migration contract. Contact: [EMAIL_1].",
    "mapping": {
      "[PERSON_1]": "Dr. Smith",
      "[PERSON_2]": "Jane Doe",
      "[EMAIL_1]": "jane.doe@company.com",
      "[PHONE_1]": "555-0199",
      "[DATE_1]": "03/15/2025",
      "[ADDRESS_1]": "28 Leopold St, Munich 80802",
      "[COMPANY_1]": "Levara",
      "[CUSTOMER_1]": "Acme Corp",
      "[PROJECT_1]": "OrcaEngine"
    }
  }'
```

**Restored result:**
```
On 03/15/2025, Dr. Smith (Levara) and Jane Doe (Acme Corp) signed a OrcaEngine
migration contract. Contact: jane.doe@company.com.
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

- The PII model is a **tool**, not a compliance guarantee (see [OpenAI notes](https://github.com/openai/privacy-filter#limitations))
- Uncommon names or regional formats may not be detected by the model — use `protected_terms` as a safety net
- Very long texts (>128K tokens) are automatically split into windows

## License

Apache 2.0 (same as OpenAI Privacy Filter)
