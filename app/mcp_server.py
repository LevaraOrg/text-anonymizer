"""MCP server exposing the anonymizer as tools for Claude Desktop and other MCP clients.

The tools call the same in-process functions as the REST API (no HTTP round-trip),
so the OPF model is loaded once and shared between the REST and MCP interfaces.

The Streamable HTTP app is mounted into the FastAPI app at /mcp (see app/main.py),
which means the single container serves both:
  - REST:  POST http://localhost:8000/anonymize  /  /deanonymize
  - MCP:   http://localhost:8000/mcp  (tools: anonymize, deanonymize)
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.anonymizer import anonymize as _anonymize
from app.deanonymizer import deanonymize as _deanonymize
from app.models import AnonymizeRequest, DeanonymizeRequest

# DNS-rebinding protection: only requests whose Host header is in the allowlist are
# accepted. Localhost is allowed by default (covers the mcp-remote / Claude Desktop
# setup). For non-localhost deployments (reverse proxy, server hostname, LAN IP),
# extend via MCP_ALLOWED_HOSTS / MCP_ALLOWED_ORIGINS — comma-separated, ":*" wildcards
# the port, e.g. MCP_ALLOWED_HOSTS="anonymizer.internal:*,10.0.0.5:8000".
_LOCALHOST_HOSTS = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
_LOCALHOST_ORIGINS = ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]


def _csv_env(name: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


_transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=_LOCALHOST_HOSTS + _csv_env("MCP_ALLOWED_HOSTS"),
    allowed_origins=_LOCALHOST_ORIGINS + _csv_env("MCP_ALLOWED_ORIGINS"),
)

# stateless_http=True keeps each request self-contained, which is what the
# mcp-remote bridge and remote connectors expect for a localhost service.
# streamable_http_path="/" makes the endpoint resolve to the mount point (/mcp)
# rather than /mcp/mcp.
mcp = FastMCP(
    "text-anonymizer",
    stateless_http=True,
    streamable_http_path="/",
    transport_security=_transport_security,
    instructions=(
        "Reversible text anonymization. Before sending sensitive text to another AI "
        "service, call `anonymize` to replace PII (names, emails, phones, addresses, "
        "dates) and user-defined business secrets (company/customer/project names) with "
        "numbered placeholders. Keep the returned `mapping`. After the AI has processed "
        "the anonymized text, call `deanonymize` with that mapping to restore the "
        "original values."
    ),
)


@mcp.tool()
def anonymize(
    text: str,
    protected_terms: dict[str, list[str]] | None = None,
    exclusions: list[str] | None = None,
    categories: list[str] | None = None,
) -> dict:
    """Anonymize text: replace PII and protected terms with reversible placeholders.

    Use this before passing sensitive text to an external AI service. The returned
    `mapping` table is required to restore the text later via `deanonymize`.

    Args:
        text: The text to anonymize.
        protected_terms: Terms to ALWAYS anonymize, grouped by custom category. Keys
            become placeholder prefixes. Use for business secrets the PII model would
            not detect, e.g. {"COMPANY": ["Levara"], "PROJECT": ["OrcaEngine"]}.
        exclusions: Terms to NEVER anonymize — they stay visible even if detected as PII.
        categories: Restrict the PII model to specific categories. None = all. Options:
            person, email_address, phone_number, private_address, url, date,
            account_number, secret.

    Returns:
        A dict with `anonymized_text`, the `mapping` table (placeholder -> original),
        detected `entities`, and which exclusions / protected terms were applied.
    """
    request = AnonymizeRequest(
        text=text,
        protected_terms=protected_terms or {},
        exclusions=exclusions or [],
        categories=categories,
    )
    return _anonymize(request).model_dump()


@mcp.tool()
def deanonymize(text: str, mapping: dict[str, str]) -> dict:
    """Restore anonymized text: replace placeholders with their original values.

    Use this after an AI service has processed anonymized text. Pass the AI output
    together with the `mapping` table returned by `anonymize`.

    Args:
        text: The anonymized (and possibly AI-processed) text containing placeholders.
        mapping: The placeholder -> original mapping table from `anonymize`.

    Returns:
        A dict with `restored_text`, the number of `replacements_made`, and any
        `unresolved_placeholders` that had no mapping entry.
    """
    request = DeanonymizeRequest(text=text, mapping=mapping)
    return _deanonymize(request).model_dump()
