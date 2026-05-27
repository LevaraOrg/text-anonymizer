from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROTECTED_TERMS_DIR = Path("/app/protected_terms")


def load_persistent_protected_terms() -> dict[str, list[str]]:
    """Load protected terms from all JSON files in the protected_terms directory."""
    terms: dict[str, list[str]] = {}
    if not PROTECTED_TERMS_DIR.exists():
        return terms

    for path in sorted(PROTECTED_TERMS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for category, values in data.items():
                    if isinstance(values, list):
                        cat = category.upper()
                        terms.setdefault(cat, [])
                        terms[cat].extend(str(t) for t in values)
        except Exception:
            logger.warning("Failed to load protected terms file: %s", path)

    total = sum(len(v) for v in terms.values())
    logger.info("Loaded %d persistent protected terms from %s", total, PROTECTED_TERMS_DIR)
    return terms


def merge_protected_terms(request_terms: dict[str, list[str]]) -> dict[str, list[str]]:
    """Merge per-request protected terms with persistent ones, deduplicated per category."""
    persistent = load_persistent_protected_terms()
    merged: dict[str, list[str]] = {}

    all_keys = set(persistent.keys()) | {k.upper() for k in request_terms}
    for cat in sorted(all_keys):
        combined = persistent.get(cat, []) + request_terms.get(cat, []) + request_terms.get(cat.lower(), [])
        merged[cat] = list(dict.fromkeys(combined))

    return merged


def find_protected_term_spans(
    text: str, protected_terms: dict[str, list[str]]
) -> list[tuple[str, str, int, int]]:
    """Find all occurrences of protected terms in text.

    Returns list of (category, matched_text, start, end) tuples, sorted by start position.
    Longer matches take priority over shorter ones at the same position.
    """
    hits: list[tuple[str, str, int, int]] = []
    text_lower = text.lower()

    for category, terms in protected_terms.items():
        for term in terms:
            term_lower = term.lower()
            start = 0
            while True:
                idx = text_lower.find(term_lower, start)
                if idx == -1:
                    break
                original = text[idx : idx + len(term)]
                hits.append((category, original, idx, idx + len(term)))
                start = idx + 1

    hits.sort(key=lambda h: (h[2], -(h[3] - h[2])))
    return _remove_overlapping_hits(hits)


def _remove_overlapping_hits(
    hits: list[tuple[str, str, int, int]],
) -> list[tuple[str, str, int, int]]:
    """Remove overlapping hits, keeping the first (longest) match at each position."""
    result: list[tuple[str, str, int, int]] = []
    last_end = -1
    for hit in hits:
        if hit[2] >= last_end:
            result.append(hit)
            last_end = hit[3]
    return result
