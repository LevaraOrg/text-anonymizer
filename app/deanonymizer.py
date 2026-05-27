from __future__ import annotations

import re

from app.models import DeanonymizeRequest, DeanonymizeResponse

PLACEHOLDER_RE = re.compile(r"\[([A-Z_]+_\d+)\]")


def deanonymize(request: DeanonymizeRequest) -> DeanonymizeResponse:
    text = request.text
    replacements = 0
    unresolved: list[str] = []

    found_placeholders = PLACEHOLDER_RE.findall(text)

    for match in found_placeholders:
        placeholder = f"[{match}]"
        if placeholder in request.mapping:
            text = text.replace(placeholder, request.mapping[placeholder])
            replacements += 1
        elif placeholder not in unresolved:
            unresolved.append(placeholder)

    return DeanonymizeResponse(
        restored_text=text,
        replacements_made=replacements,
        unresolved_placeholders=unresolved,
    )
