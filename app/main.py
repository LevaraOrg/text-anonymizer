from __future__ import annotations

import logging

from fastapi import Body, FastAPI

from app.anonymizer import anonymize, get_opf
from app.deanonymizer import deanonymize
from app.models import (
    ANONYMIZE_EXAMPLE_CATEGORY_FILTER,
    ANONYMIZE_EXAMPLE_WITH_EXCLUSIONS,
    ANONYMIZE_EXAMPLE_WITHOUT_EXCLUSIONS,
    DEANONYMIZE_EXAMPLE,
    AnonymizeRequest,
    AnonymizeResponse,
    DeanonymizeRequest,
    DeanonymizeResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Text Anonymizer",
    description=(
        "Reversible text anonymization with exclusion lists. Wraps OpenAI Privacy Filter.\n\n"
        "**Workflow:** Send text to `/anonymize` → get anonymized text + mapping table → "
        "send anonymized text to AI → send AI result + mapping to `/deanonymize` → get restored text.\n\n"
        "**Test the exclusion effect:** Use the example dropdown in `/anonymize` below. "
        "Compare 'With exclusions' vs 'Without exclusions' on the same text to see which terms are preserved."
    ),
    version="1.0.0",
)


@app.post("/anonymize", response_model=AnonymizeResponse)
def handle_anonymize(
    request: AnonymizeRequest = Body(
        openapi_examples={
            "with_exclusions": ANONYMIZE_EXAMPLE_WITH_EXCLUSIONS,
            "without_exclusions": ANONYMIZE_EXAMPLE_WITHOUT_EXCLUSIONS,
            "category_filter": ANONYMIZE_EXAMPLE_CATEGORY_FILTER,
        },
    ),
) -> AnonymizeResponse:
    return anonymize(request)


@app.post("/deanonymize", response_model=DeanonymizeResponse)
def handle_deanonymize(
    request: DeanonymizeRequest = Body(
        openapi_examples={
            "restore_ai_output": DEANONYMIZE_EXAMPLE,
        },
    ),
) -> DeanonymizeResponse:
    return deanonymize(request)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/warmup")
def warmup() -> dict[str, str]:
    get_opf()
    return {"status": "model loaded"}
