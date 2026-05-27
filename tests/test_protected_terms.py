from app.protected_terms import find_protected_term_spans, _remove_overlapping_hits


def test_find_single_term():
    spans = find_protected_term_spans(
        "We signed a deal with Levara last week.",
        {"COMPANY": ["Levara"]},
    )
    assert len(spans) == 1
    assert spans[0] == ("COMPANY", "Levara", 22, 28)


def test_find_multiple_categories():
    spans = find_protected_term_spans(
        "Levara is working with Acme Corp on OrcaEngine.",
        {"COMPANY": ["Levara"], "CUSTOMER": ["Acme Corp"], "PROJECT": ["OrcaEngine"]},
    )
    assert len(spans) == 3
    categories = [s[0] for s in spans]
    assert "COMPANY" in categories
    assert "CUSTOMER" in categories
    assert "PROJECT" in categories


def test_case_insensitive():
    spans = find_protected_term_spans(
        "LEVARA and levara are the same.",
        {"COMPANY": ["Levara"]},
    )
    assert len(spans) == 2
    assert spans[0][2] == 0
    assert spans[1][2] == 11


def test_multiple_occurrences():
    spans = find_protected_term_spans(
        "Levara contacted Levara about the Levara project.",
        {"COMPANY": ["Levara"]},
    )
    assert len(spans) == 3


def test_no_match():
    spans = find_protected_term_spans(
        "Nothing special here.",
        {"COMPANY": ["Levara"]},
    )
    assert spans == []


def test_overlapping_terms_longer_wins():
    spans = find_protected_term_spans(
        "Contact Acme Corp International for details.",
        {"CUSTOMER": ["Acme Corp", "Acme Corp International"]},
    )
    assert len(spans) == 1
    assert spans[0][1] == "Acme Corp International"


def test_remove_overlapping_hits():
    hits = [
        ("A", "Acme Corp International", 8, 31),
        ("A", "Acme Corp", 8, 17),
    ]
    result = _remove_overlapping_hits(hits)
    assert len(result) == 1
    assert result[0][1] == "Acme Corp International"
