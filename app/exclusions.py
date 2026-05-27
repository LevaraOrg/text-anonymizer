from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

EXCLUSIONS_DIR = Path("/app/exclusions")


def load_persistent_exclusions() -> list[str]:
    """Load exclusion terms from all JSON files in the exclusions directory."""
    terms: list[str] = []
    if not EXCLUSIONS_DIR.exists():
        return terms

    for path in sorted(EXCLUSIONS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                terms.extend(str(t) for t in data)
            elif isinstance(data, dict):
                for values in data.values():
                    if isinstance(values, list):
                        terms.extend(str(t) for t in values)
        except Exception:
            logger.warning("Failed to load exclusion file: %s", path)

    logger.info("Loaded %d persistent exclusion terms from %s", len(terms), EXCLUSIONS_DIR)
    return terms


def merge_exclusions(request_exclusions: list[str]) -> list[str]:
    """Merge per-request exclusions with persistent ones, deduplicated."""
    persistent = load_persistent_exclusions()
    combined = list(dict.fromkeys(persistent + request_exclusions))
    return combined


def find_exclusion_ranges(text: str, exclusions: list[str]) -> list[tuple[int, int]]:
    """Find all character ranges in text that match exclusion terms."""
    ranges: list[tuple[int, int]] = []
    text_lower = text.lower()
    for term in exclusions:
        term_lower = term.lower()
        start = 0
        while True:
            idx = text_lower.find(term_lower, start)
            if idx == -1:
                break
            ranges.append((idx, idx + len(term)))
            start = idx + 1
    return ranges


def overlaps_exclusion(span_start: int, span_end: int, exclusion_ranges: list[tuple[int, int]]) -> bool:
    """Check if a detected span overlaps with any exclusion range."""
    for ex_start, ex_end in exclusion_ranges:
        if span_start < ex_end and span_end > ex_start:
            return True
    return False
