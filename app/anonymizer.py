from __future__ import annotations

import logging
from collections import defaultdict

from app.exclusions import find_exclusion_ranges, merge_exclusions, overlaps_exclusion
from app.models import AnonymizeRequest, AnonymizeResponse, DetectedEntity

logger = logging.getLogger(__name__)

_opf_instance = None

CATEGORY_MAP = {
    "account_number": "ACCOUNT",
    "private_address": "ADDRESS",
    "email_address": "EMAIL",
    "person": "PERSON",
    "phone_number": "PHONE",
    "url": "URL",
    "date": "DATE",
    "secret": "SECRET",
}


def get_opf():
    from opf import OPF

    global _opf_instance
    if _opf_instance is None:
        logger.info("Initializing OPF model (first request, this may take a moment)...")
        _opf_instance = OPF(device="cpu", output_mode="typed")
    return _opf_instance


def anonymize(request: AnonymizeRequest) -> AnonymizeResponse:
    opf = get_opf()
    result = opf.redact(request.text)

    exclusions = merge_exclusions(request.exclusions)
    exclusion_ranges = find_exclusion_ranges(request.text, exclusions) if exclusions else []

    counters: dict[str, int] = defaultdict(int)
    entities: list[DetectedEntity] = []
    mapping: dict[str, str] = {}

    spans = sorted(result.detected_spans, key=lambda s: s.start)

    for span in spans:
        label = span.label.lower() if hasattr(span, "label") else "unknown"

        if request.categories and label not in request.categories:
            continue

        if overlaps_exclusion(span.start, span.end, exclusion_ranges):
            continue

        tag = CATEGORY_MAP.get(label, label.upper())
        counters[tag] += 1
        placeholder = f"[{tag}_{counters[tag]}]"
        original_text = request.text[span.start : span.end]

        mapping[placeholder] = original_text
        entities.append(
            DetectedEntity(
                placeholder=placeholder,
                original=original_text,
                category=label,
                start=span.start,
                end=span.end,
            )
        )

    anonymized = _replace_spans(request.text, entities)

    return AnonymizeResponse(
        anonymized_text=anonymized,
        mapping=mapping,
        entities=entities,
        exclusions_applied=exclusions,
    )



def _replace_spans(text: str, entities: list[DetectedEntity]) -> str:
    """Replace detected spans in text with placeholders, working from end to start to preserve offsets."""
    result = text
    for entity in sorted(entities, key=lambda e: e.start, reverse=True):
        result = result[: entity.start] + entity.placeholder + result[entity.end :]
    return result
