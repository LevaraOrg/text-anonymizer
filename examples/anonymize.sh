#!/bin/bash
# Anonymize text with protected business terms and PII detection
curl -s -X POST http://localhost:8000/anonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Sarah Miller from Levara signed the OrcaEngine contract with Acme Corp. Contact: sarah.miller@levara.cloud, +1 555-0198. Meeting at 742 Evergreen Terrace, Springfield, IL 62704 on 06/15/2025.",
    "protected_terms": {
      "COMPANY": ["Levara"],
      "CUSTOMER": ["Acme Corp"],
      "PROJECT": ["OrcaEngine"]
    }
  }' | python3 -m json.tool
