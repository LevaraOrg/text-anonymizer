from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Body, FastAPI

from app.anonymizer import anonymize, get_opf
from app.deanonymizer import deanonymize
from app.mcp_server import mcp
from app.models import (
    ANONYMIZE_EXAMPLE_COMBINED,
    ANONYMIZE_EXAMPLE_PLAIN,
    ANONYMIZE_EXAMPLE_PROTECTED,
    DEANONYMIZE_EXAMPLE,
    AnonymizeRequest,
    AnonymizeResponse,
    DeanonymizeRequest,
    DeanonymizeResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# The mounted MCP app manages its own Streamable HTTP session manager, whose
# lifecycle must run inside the parent app's lifespan (Starlette does not run a
# sub-app's lifespan automatically).
mcp_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="Text Anonymizer",
    description=(
        "Reversible text anonymization with **protected terms** and exclusion lists. "
        "Wraps OpenAI Privacy Filter.\n\n"
        "**Two anonymization modes:**\n"
        "- **PII model** — automatically detects persons, emails, phones, addresses, dates, etc.\n"
        "- **Protected terms** — YOU define business secrets, company names, customer names, "
        "project codes, or domain jargon that must always be anonymized\n\n"
        "**Workflow:** `/anonymize` (text + protected terms) → send anonymized text to AI → "
        "`/deanonymize` (AI result + mapping) → restored text with all originals back.\n\n"
        "**Try it:** Use the example dropdown on `/anonymize` below — "
        "compare 'Protected terms' vs 'Plain' to see business secrets being masked.\n\n"
        "**MCP:** the same tools are exposed for AI clients (e.g. Claude Desktop) at `/mcp`."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# MCP Streamable HTTP endpoint: http://localhost:8000/mcp
app.mount("/mcp", mcp_app)


@app.post("/anonymize", response_model=AnonymizeResponse)
def handle_anonymize(
    request: AnonymizeRequest = Body(
        openapi_examples={
            "protected_terms": ANONYMIZE_EXAMPLE_PROTECTED,
            "combined": ANONYMIZE_EXAMPLE_COMBINED,
            "plain": ANONYMIZE_EXAMPLE_PLAIN,
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
