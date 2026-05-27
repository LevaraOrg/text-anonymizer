#!/bin/bash
# Restore anonymized text after AI processing
curl -s -X POST http://localhost:8000/deanonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Die KI empfiehlt, dass [PERSON_1] per [EMAIL_1] kontaktiert wird. Die Adresse [ADDRESS_1] wurde verifiziert.",
    "mapping": {
      "[PERSON_1]": "Max Mustermann",
      "[EMAIL_1]": "max.mustermann@example.com",
      "[ADDRESS_1]": "Hauptstraße 42, 10115 Berlin"
    }
  }' | python3 -m json.tool
