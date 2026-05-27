#!/bin/bash
# Anonymize text with exclusions
curl -s -X POST http://localhost:8000/anonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bitte kontaktieren Sie Max Mustermann unter max.mustermann@example.com oder +49 171 1234567. Er arbeitet bei Levara in der Hauptstraße 42, 10115 Berlin.",
    "exclusions": ["Levara"]
  }' | python3 -m json.tool
