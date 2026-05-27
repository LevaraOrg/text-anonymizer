#!/bin/bash
# Restore anonymized text after AI processing
curl -s -X POST http://localhost:8000/deanonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The AI recommends contacting [PERSON_1] via [EMAIL_1]. The address [ADDRESS_1] has been verified.",
    "mapping": {
      "[PERSON_1]": "John Smith",
      "[EMAIL_1]": "john.smith@example.com",
      "[ADDRESS_1]": "42 Main Street, New York, NY 10001"
    }
  }' | python3 -m json.tool
