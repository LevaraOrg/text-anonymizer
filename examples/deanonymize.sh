#!/bin/bash
# Restore anonymized text after AI processing
curl -s -X POST http://localhost:8000/deanonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Summary: [PERSON_1] from [COMPANY_1] confirmed the [PROJECT_1] contract with [CUSTOMER_1]. Contact via [EMAIL_1].",
    "mapping": {
      "[PERSON_1]": "Sarah Miller",
      "[COMPANY_1]": "Levara",
      "[PROJECT_1]": "OrcaEngine",
      "[CUSTOMER_1]": "Acme Corp",
      "[EMAIL_1]": "sarah.miller@levara.cloud",
      "[PHONE_1]": "+1 555-0198",
      "[ADDRESS_1]": "742 Evergreen Terrace, Springfield, IL 62704",
      "[DATE_1]": "06/15/2025"
    }
  }' | python3 -m json.tool
