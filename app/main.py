from __future__ import annotations

import logging

from fastapi import FastAPI

from app.anonymizer import anonymize, get_opf
from app.deanonymizer import deanonymize
from app.models import AnonymizeRequest, AnonymizeResponse, DeanonymizeRequest, DeanonymizeResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Text Anonymizer",
    description="Reversible text anonymization with exclusion lists. Wraps OpenAI Privacy Filter.",
    version="1.0.0",
)


@app.post("/anonymize", response_model=AnonymizeResponse)
def handle_anonymize(request: AnonymizeRequest) -> AnonymizeResponse:
    return anonymize(request)


@app.post("/deanonymize", response_model=DeanonymizeResponse)
def handle_deanonymize(request: DeanonymizeRequest) -> DeanonymizeResponse:
    return deanonymize(request)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/warmup")
def warmup() -> dict[str, str]:
    get_opf()
    return {"status": "model loaded"}
