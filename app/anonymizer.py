from __future__ import annotations

import logging
from collections import defaultdict

from app.exclusions import find_exclusion_ranges, merge_exclusions, overlaps_exclusion
from app.models import AnonymizeRequest, AnonymizeResponse, DetectedEntity
from app.protected_terms import find_protected_term_spans, merge_protected_terms

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

    protected = merge_protected_terms(request.protected_terms)
    custom_spans = find_protected_term_spans(request.text, protected) if protected else []

    counters: dict[str, int] = defaultdict(int)
    entities: list[DetectedEntity] = []
    mapping: dict[str, str] = {}

    raw_spans: list[tuple[str, str, int, int]] = []

    for span in result.detected_spans:
        label = span.label.lower() if hasattr(span, "label") else "unknown"

        if request.categories and label not in request.categories:
            continue

        if overlaps_exclusion(span.start, span.end, exclusion_ranges):
            continue

        tag = CATEGORY_MAP.get(label, label.upper())
        original_text = request.text[span.start : span.end]
        raw_spans.append((tag, original_text, span.start, span.end))

    for category, original_text, start, end in custom_spans:
        raw_spans.append((category, original_text, start, end))

    merged = _merge_spans(raw_spans)

    for tag, original_text, start, end in merged:
        counters[tag] += 1
        placeholder = f"[{tag}_{counters[tag]}]"
        mapping[placeholder] = original_text
        entities.append(
            DetectedEntity(
                placeholder=placeholder,
                original=original_text,
                category=tag.lower(),
                start=start,
                end=end,
            )
        )

    anonymized = _replace_spans(request.text, entities)

    return AnonymizeResponse(
        anonymized_text=anonymized,
        mapping=mapping,
        entities=entities,
        exclusions_applied=exclusions,
        protected_terms_applied=protected,
    )


def _merge_spans(spans: list[tuple[str, str, int, int]]) -> list[tuple[str, str, int, int]]:
    """Merge PII and custom spans, removing overlaps. Earlier/longer spans win."""
    sorted_spans = sorted(spans, key=lambda s: (s[2], -(s[3] - s[2])))
    result: list[tuple[str, str, int, int]] = []
    last_end = -1
    for span in sorted_spans:
        if span[2] >= last_end:
            result.append(span)
            last_end = span[3]
    return result


def _replace_spans(text: str, entities: list[DetectedEntity]) -> str:
    result = text
    for entity in sorted(entities, key=lambda e: e.start, reverse=True):
        result = result[: entity.start] + entity.placeholder + result[entity.end :]
    return result
