#!/bin/bash
# Anonymize text with exclusions
curl -s -X POST http://localhost:8000/anonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Please contact John Smith at john.smith@example.com or +1 555-0123. He works at Levara, 42 Main Street, New York, NY 10001.",
    "exclusions": ["Levara"]
  }' | python3 -m json.tool
